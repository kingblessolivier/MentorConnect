"""
Feed App Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse_lazy

from .models import Post, Comment, Like


class FeedView(ListView):
    """Main feed view - accessible to everyone"""
    template_name = 'feed/feed_public.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(is_active=True).select_related('author', 'shared_post__author')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get user's liked posts
        if self.request.user.is_authenticated:
            context['liked_posts'] = set(
                Like.objects.filter(user=self.request.user, post__isnull=False)
                .values_list('post_id', flat=True)
            )

            # Get suggestions based on user profile
            from profiles.models import MentorProfile
            user = self.request.user

            # Get recommended mentors based on skills/interests
            recommended = MentorProfile.objects.filter(
                is_available=True
            ).exclude(user=user).select_related('user')[:5]

            context['recommended_mentors'] = recommended
        else:
            context['liked_posts'] = set()
            # Show some mentors for non-logged users
            from profiles.models import MentorProfile
            context['recommended_mentors'] = MentorProfile.objects.filter(
                is_available=True
            ).select_related('user')[:5]

        return context


class CreatePostView(LoginRequiredMixin, CreateView):
    """Create a new post"""
    model = Post
    template_name = 'feed/create_post.html'
    fields = ['content', 'image']
    success_url = reverse_lazy('feed:home')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Post created successfully!')
        return super().form_valid(form)


class PostDetailView(DetailView):
    """View a single post with comments - accessible to everyone"""
    model = Post
    template_name = 'feed/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.filter(
            is_active=True, parent__isnull=True
        ).select_related('author')

        # Check if user is authenticated before checking likes
        if self.request.user.is_authenticated:
            context['is_liked'] = Like.objects.filter(
                user=self.request.user, post=self.object
            ).exists()
        else:
            context['is_liked'] = False
        return context


@login_required
def delete_post(request, pk):
    """Delete a post"""
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user and not request.user.is_admin_user:
        messages.error(request, 'You cannot delete this post.')
        return redirect('feed:home')
    post.is_active = False
    post.save()
    messages.success(request, 'Post deleted.')
    return redirect('feed:home')


@login_required
def toggle_like(request, pk):
    """Toggle like on a post"""
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        # Notify post author
        if post.author != request.user:
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='like',
                    message=f'{request.user.get_full_name()} liked your post.'
                )
            except Exception:
                pass

    post.update_counts()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'likes_count': post.likes_count})
    return redirect('feed:post_detail', pk=pk)


@login_required
def add_comment(request, pk):
    """Add a comment to a post"""
    if request.method != 'POST':
        return redirect('feed:post_detail', pk=pk)

    post = get_object_or_404(Post, pk=pk)
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')

    if not content:
        messages.error(request, 'Comment cannot be empty.')
        # Redirect back to referrer or post detail
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return redirect(referer)
        return redirect('feed:post_detail', pk=pk)

    parent = None
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id)

    comment = Comment.objects.create(
        post=post, author=request.user, content=content, parent=parent
    )

    # Update post counts
    post.update_counts()

    # Notify post author
    if post.author != request.user:
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='comment',
                message=f'{request.user.get_full_name()} commented on your post.'
            )
        except Exception:
            pass

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'comment_id': comment.id,
            'author': request.user.get_full_name(),
            'avatar': request.user.get_avatar_url(),
            'content': content,
            'comments_count': post.comments_count
        })

    messages.success(request, 'Comment added!')
    # Redirect back to referrer or post detail
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('feed:post_detail', pk=pk)


@login_required
def delete_comment(request, pk):
    """Delete a comment"""
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk

    if comment.author != request.user and not request.user.is_admin_user:
        messages.error(request, 'You cannot delete this comment.')
        return redirect('feed:post_detail', pk=post_pk)

    comment.is_active = False
    comment.save()
    messages.success(request, 'Comment deleted.')
    return redirect('feed:post_detail', pk=post_pk)


@login_required
def share_post(request, pk):
    """Share/repost a post"""
    original_post = get_object_or_404(Post, pk=pk)
    comment = request.POST.get('comment', '')

    # Create a new post that references the original
    new_post = Post.objects.create(
        author=request.user,
        content=comment,
        shared_post=original_post
    )

    original_post.update_counts()

    # Notify original author
    if original_post.author != request.user:
        try:
            from notifications.models import Notification
            Notification.objects.create(
                recipient=original_post.author,
                sender=request.user,
                notification_type='share',
                message=f'{request.user.get_full_name()} shared your post.'
            )
        except Exception:
            pass

    messages.success(request, 'Post shared!')
    return redirect('feed:home')
