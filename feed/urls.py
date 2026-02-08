"""
Feed App URLs
"""

from django.urls import path
from . import views

app_name = 'feed'

urlpatterns = [
    path('', views.FeedView.as_view(), name='home'),
    path('post/create/', views.CreatePostView.as_view(), name='create_post'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('post/<int:pk>/share/', views.share_post, name='share_post'),
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete_comment'),
]
