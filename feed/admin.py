from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Post, Comment, Like


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin for Feed Posts
    """
    list_display = (
        'author_display',
        'content_preview',
        'engagement_stats',
        'is_pinned_badge',
        'is_active_badge',
        'created_at_short',
    )
    list_filter = ('is_active', 'is_pinned', 'created_at')
    search_fields = ('author__first_name', 'author__last_name', 'author__email', 'content')
    readonly_fields = ('likes_count', 'comments_count', 'shares_count', 'created_at', 'updated_at')
    ordering = ('-is_pinned', '-created_at')

    fieldsets = (
        (_('Post Information'), {
            'fields': ('author', 'content', 'image'),
            'classes': ('wide',)
        }),
        (_('Engagement'), {
            'fields': ('likes_count', 'comments_count', 'shares_count'),
            'classes': ('wide',)
        }),
        (_('Sharing'), {
            'fields': ('shared_post',),
            'classes': ('wide',)
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_pinned'),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def author_display(self, obj):
        return obj.author.get_full_name()
    author_display.short_description = _('Author')
    author_display.admin_order_field = 'author__first_name'

    def content_preview(self, obj):
        preview = obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
        return preview
    content_preview.short_description = _('Content')

    def engagement_stats(self, obj):
        return format_html(
            '❤️ {} | 💬 {} | 🔄 {}',
            obj.likes_count, obj.comments_count, obj.shares_count
        )
    engagement_stats.short_description = _('Likes | Comments | Shares')

    def is_pinned_badge(self, obj):
        if obj.is_pinned:
            return format_html('<span style="color: #F59E0B; font-weight: bold;">📌 Pinned</span>')
        return '—'
    is_pinned_badge.short_description = _('Pinned')

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓ Active</span>')
        return format_html('<span style="color: #EF4444; font-weight: bold;">✗ Hidden</span>')
    is_active_badge.short_description = _('Status')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_short.short_description = _('Posted')
    created_at_short.admin_order_field = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin for Post Comments
    """
    list_display = (
        'author_display',
        'post_link',
        'content_preview',
        'likes_count_display',
        'is_active_badge',
        'created_at_short',
    )
    list_filter = ('is_active', 'created_at', 'post')
    search_fields = ('author__first_name', 'author__last_name', 'author__email', 'content')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        (_('Comment Information'), {
            'fields': ('post', 'author', 'content'),
            'classes': ('wide',)
        }),
        (_('Threading'), {
            'fields': ('parent',),
            'classes': ('wide',)
        }),
        (_('Engagement'), {
            'fields': ('likes_count',),
            'classes': ('wide',)
        }),
        (_('Status'), {
            'fields': ('is_active',),
            'classes': ('wide',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'collapse'),
        }),
    )

    def author_display(self, obj):
        return obj.author.get_full_name()
    author_display.short_description = _('Author')

    def post_link(self, obj):
        return f"Post #{obj.post.id}"
    post_link.short_description = _('Post')

    def content_preview(self, obj):
        preview = obj.content[:40] + '...' if len(obj.content) > 40 else obj.content
        return preview
    content_preview.short_description = _('Comment')

    def likes_count_display(self, obj):
        return format_html('<span style="color: #EC4899; font-weight: bold;">❤️ {}</span>', obj.likes_count)
    likes_count_display.short_description = _('Likes')

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #10B981; font-weight: bold;">✓</span>')
        return format_html('<span style="color: #EF4444; font-weight: bold;">✗</span>')
    is_active_badge.short_description = _('Active')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_short.short_description = _('Posted')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """
    Admin for Likes
    """
    list_display = ('user_display', 'like_type', 'created_at_short')
    list_filter = ('created_at', 'post')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def user_display(self, obj):
        return obj.user.get_full_name()
    user_display.short_description = _('User')

    def like_type(self, obj):
        if obj.post:
            return format_html('❤️ Post')
        elif obj.comment:
            return format_html('❤️ Comment')
        return '—'
    like_type.short_description = _('Liked')

    def created_at_short(self, obj):
        return obj.created_at.strftime('%b %d, %Y %H:%M')
    created_at_short.short_description = _('Timestamp')
