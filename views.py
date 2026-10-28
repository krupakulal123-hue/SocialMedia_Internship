
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Post, Comment, Like, Follow


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('feed')
    else:
        form = UserCreationForm()

    return render(request, 'posts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return redirect('feed')
    else:
        form = AuthenticationForm(request)

    return render(request, 'posts/login.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def feed_view(request):
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()

        if content:
            Post.objects.create(
                author=request.user,
                content=content
            )
            messages.success(request, 'Your post was published!')
            return redirect('feed')

        messages.error(request, 'Please write something before posting.')

    posts = Post.objects.select_related('author').prefetch_related(
        'comments__author', 'likes'
    ).order_by('-created_at')

    return render(request, 'posts/feed.html', {'posts': posts})


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    content = request.POST.get('content', '').strip()

    if content:
        Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )

    return redirect('feed')


@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user
    )

    if not created:
        like.delete()

    return redirect('feed')


@login_required
def users_view(request):
    users = User.objects.exclude(
        id=request.user.id
    ).order_by('username')

    followed_ids = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)

    return render(request, 'posts/users.html', {
        'users': users,
        'followed_ids': followed_ids,
    })


@login_required
@require_POST
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        messages.error(request, 'You cannot follow yourself.')
        return redirect('users')

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )

    if not created:
        follow.delete()
        messages.success(
            request,
            f'You unfollowed {target_user.username}.'
        )
    else:
        messages.success(
            request,
            f'You are now following {target_user.username}.'
        )

    return redirect('users')


@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(
        User,
        username=username
    )

    posts = Post.objects.filter(
        author=profile_user
    ).select_related('author').prefetch_related(
        'comments__author',
        'likes'
    ).order_by('-created_at')

    is_following = Follow.objects.filter(
        follower=request.user,
        following=profile_user
    ).exists()

    return render(request, 'posts/profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
    })
