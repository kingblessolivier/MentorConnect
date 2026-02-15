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
        return Post.objects.filter(is_active=True, is_approved=True).select_related('author', 'shared_post__author')

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

        # Add trending hashtags
        context['trending_hashtags'] = self.get_trending_hashtags()
        return context

    def get_trending_hashtags(self, limit=5):
        """Extract top hashtags from recent posts"""
        from django.utils import timezone
        from datetime import timedelta
        import re

        # Get posts from the last 7 days (or all time if fewer)
        week_ago = timezone.now() - timedelta(days=7)
        posts = Post.objects.filter(
            is_active=True,
            is_approved=True,
            created_at__gte=week_ago
        ).values_list('content', flat=True)

        hashtag_counter = {}
        hashtag_pattern = re.compile(r'#(\w+)')
        for content in posts:
            matches = hashtag_pattern.findall(content)
            for tag in matches:
                tag_lower = tag.lower()
                hashtag_counter[tag_lower] = hashtag_counter.get(tag_lower, 0) + 1

        # Sort by count descending, then alphabetically
        sorted_tags = sorted(hashtag_counter.items(), key=lambda x: (-x[1], x[0]))
        top_tags = sorted_tags[:limit]
        # Format as list of dicts with tag and count
        trending = [{'tag': tag, 'count': count} for tag, count in top_tags]
        return trending


class CreatePostView(LoginRequiredMixin, CreateView):
    """Create a new post"""
    model = Post
    template_name = 'feed/create_post.html'
    fields = ['content', 'image']
    success_url = reverse_lazy('feed:home')

    def form_valid(self, form):
        from django.utils import timezone
        form.instance.author = self.request.user
        # Auto-approve posts from mentors, admins, facilitators, finance officers, mentorship department
        if self.request.user.role in ['mentor', 'admin', 'mentor_facilitator', 'finance_manager', 'mentorship_department']:
            form.instance.is_approved = True
            form.instance.approved_at = timezone.now()
            form.instance.approved_by = self.request.user
        else:
            form.instance.is_approved = False
        if self.request.user.role in ['mentor', 'admin', 'mentor_facilitator', 'finance_manager', 'mentorship_department']:
            messages.success(self.request, 'Post created successfully!')
        else:
            messages.success(self.request, 'Post created successfully! It will be visible after admin approval.')
        return super().form_valid(form)


class PostDetailView(DetailView):
    """View a single post with comments - accessible to everyone"""
    model = Post
    template_name = 'feed/post_detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        user = self.request.user
        # If post is approved, allow viewing
        if post.is_approved:
            return post
        # If user is admin or author, allow viewing
        if user.is_authenticated and (user.is_admin_user or user == post.author):
            return post
        # Otherwise, raise 404
        from django.http import Http404
        raise Http404("Post not found")

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
    from django.utils import timezone
    new_post = Post.objects.create(
        author=request.user,
        content=comment,
        shared_post=original_post,
        is_active=True,
        is_approved=request.user.role in ['mentor', 'admin', 'mentor_facilitator', 'finance_manager', 'mentorship_department'],
        approved_at=timezone.now() if request.user.role in ['mentor', 'admin', 'mentor_facilitator', 'finance_manager', 'mentorship_department'] else None,
        approved_by=request.user if request.user.role in ['mentor', 'admin', 'mentor_facilitator', 'finance_manager', 'mentorship_department'] else None
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
