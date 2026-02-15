"""
Profiles App URLs
"""

from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # View profiles
    path('<int:pk>/', views.ProfileDetailView.as_view(), name='detail'),
    path('mentor/<int:pk>/', views.MentorProfileView.as_view(), name='mentor_detail'),
    path('student/<int:pk>/', views.StudentProfileView.as_view(), name='student_detail'),

    # Edit profiles
    path('edit/', views.ProfileEditView.as_view(), name='edit'),
    path('student/edit/', views.StudentProfileEditView.as_view(), name='student_edit'),
    path('mentor/edit/', views.MentorProfileEditView.as_view(), name='mentor_edit'),

    # Application pages
    path('apply-as-mentor/', views.ApplyAsMentorView.as_view(), name='apply_as_mentor'),
    path('apply-for-mentorship/', views.ApplyForMentorshipView.as_view(), name='apply_for_mentorship'),

    # Follow/Unfollow
    path('follow/<int:user_id>/', views.follow_user, name='follow'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow'),
    path('followers/', views.FollowersListView.as_view(), name='followers'),
    path('following/', views.FollowingListView.as_view(), name='following'),
]
