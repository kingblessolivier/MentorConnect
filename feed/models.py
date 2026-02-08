"""
Feed App Models
LinkedIn-style feed with posts, comments, likes, shares
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Post(models.Model):
    """
    Feed post by mentors or students
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField(verbose_name=_('Post Content'))
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    # Engagement
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)

    # Shared post (for reposts)
    shared_post = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='shares'
    )

    # Status
    is_active = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        return f"{self.author.get_full_name()}: {self.content[:50]}..."

    def update_counts(self):
        """Update engagement counts"""
        self.likes_count = self.post_likes.count()
        self.comments_count = self.comments.filter(is_active=True).count()
        self.shares_count = Post.objects.filter(shared_post=self).count()
        self.save(update_fields=['likes_count', 'comments_count', 'shares_count'])


class Comment(models.Model):
    """
    Comment on a post
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField(max_length=1000)

    # For nested comments
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies'
    )

    likes_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on post {self.post.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.post.update_counts()


class Like(models.Model):
    """
    Like on a post or comment
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, null=True, blank=True, related_name='post_likes'
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='comment_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'post'], ['user', 'comment']]

    def __str__(self):
        if self.post:
            return f"{self.user.get_full_name()} likes post {self.post.id}"
        return f"{self.user.get_full_name()} likes comment {self.comment.id}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.post:
            self.post.update_counts()
        elif self.comment:
            self.comment.likes_count = self.comment.comment_likes.count()
            self.comment.save(update_fields=['likes_count'])
