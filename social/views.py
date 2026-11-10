from .models import Notification
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Message
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Post, Like, Comment, Profile, Follow


def home(request):
    posts = Post.objects.select_related('author').prefetch_related(
        'comments', 'likes'
    ).order_by('-created_at')

    return render(request, 'social/home.html', {'posts': posts})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'social/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'social/login.html', {'form': form})


@require_POST
def user_logout(request):
    if request.user.is_authenticated:
        logout(request)

    return redirect('home')



@login_required
@require_POST
def create_post(request):
    content = request.POST.get('content', '').strip()
    image_url = request.POST.get('image_url', '').strip()
    image = request.FILES.get('image')

    if image:
        if image.content_type not in [
            'image/jpeg',
            'image/png',
            'image/webp'
        ]:
            return redirect('home')

        if image.size > 5 * 1024 * 1024:
            return redirect('home')

    if content or image_url or image:
        Post.objects.create(
            author=request.user,
            content=content,
            image_url=image_url,
            image=image
        )

    return redirect('home')



@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like, created = Like.objects.get_or_create(
        post=post,
        user=request.user
    )

    if created:
        # Apni post ko like karne par notification nahi aayega
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='like',
                message=f'{request.user.username} liked your post.',
                link=f'/users/{request.user.username}/'
            )
    else:
        # Unlike karne par like delete hoga
        like.delete()

    return redirect('home')


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    content = request.POST.get('content', '').strip()

    if content and len(content) <= 500:
        Comment.objects.create(
            post=post,
            author=request.user,
            content=content
        )

    return redirect('home')


@login_required
def profile(request):
    user_profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        bio = request.POST.get('bio', '').strip()
        photo = request.FILES.get('profile_image')

        if len(bio) <= 300:
            user_profile.bio = bio

            if photo:
                if photo.content_type not in [
                    'image/jpeg',
                    'image/png',
                    'image/webp'
                ]:
                    return render(request, 'social/profile.html', {
                        'profile_user': request.user,
                        'profile': user_profile,
                        'error': 'Please select a JPG, PNG, or WebP image.'
                    })

                if photo.size > 5 * 1024 * 1024:
                    return render(request, 'social/profile.html', {
                        'profile_user': request.user,
                        'profile': user_profile,
                        'error': 'Photo size must be 5 MB or less.'
                    })

                user_profile.profile_image = photo

            user_profile.save()
            return redirect('profile')

    return render(request, 'social/profile.html', {
        'profile_user': request.user,
        'profile': user_profile,
    })


@login_required
def user_profile(request, username):
    from django.contrib.auth.models import User

    profile_user = get_object_or_404(User, username=username)

    user_profile, created = Profile.objects.get_or_create(
        user=profile_user
    )

    posts = Post.objects.filter(
        author=profile_user
    ).order_by('-created_at')

    is_following = False

    if request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user
        ).exists()

    followers_count = Follow.objects.filter(
        following=profile_user
    ).count()

    following_count = Follow.objects.filter(
        follower=profile_user
    ).count()

    return render(request, 'social/user_profile.html', {
        'profile_user': profile_user,
        'profile': user_profile,
        'posts': posts,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
    })



@login_required
@require_POST
def toggle_follow(request, username):
    from django.contrib.auth.models import User

    target_user = get_object_or_404(User, username=username)

    if request.user == target_user:
        return redirect('user_profile', username=username)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user
    )

    if created:
        Notification.objects.create(
            recipient=target_user,
            sender=request.user,
            notification_type='follow',
            message=f'{request.user.username} started following you.',
            link=f'/users/{request.user.username}/'
        )
    else:
        follow.delete()

    return redirect('user_profile', username=username)


@login_required
def inbox(request):
    messages = Message.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user)
    ).order_by('-created_at')

    contacts = User.objects.filter(
        Q(sent_messages__receiver=request.user) |
        Q(received_messages__sender=request.user)
    ).distinct()

    return render(request, 'social/inbox.html', {
        'contacts': contacts,
        'messages': messages,
    })


@login_required
def chat(request, username):
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        return redirect('inbox')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()

        if content and len(content) <= 2000:
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content
            )

        return redirect('chat', username=other_user.username)

    conversation = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')

    conversation.filter(
        sender=other_user,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)

    return render(request, 'social/chat.html', {
        'other_user': other_user,
        'conversation': conversation,
    })

@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(
        recipient=request.user
    )

    # Notifications ko read mark karo
    user_notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'social/notifications.html', {
        'user_notifications': user_notifications,
    })
