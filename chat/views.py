
"""
Chat App Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, Max
from django.utils import timezone

from accounts.models import User
from .models import Conversation, Message



class ConversationListView(LoginRequiredMixin, ListView):
    """List all conversations"""
    template_name = 'chat/list.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages').annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time', '-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get users the current user already has conversations with
        existing_conversations = Conversation.objects.filter(participants=user)
        users_with_conversations = User.objects.filter(
            conversations__in=existing_conversations
        ).exclude(id=user.id).values_list('id', flat=True)

        # Suggest users to start conversations with based on role
        if user.is_student:
            # Students see mentors they can message
            suggested_users = User.objects.filter(
                role='mentor',
                is_active=True
            ).exclude(
                id__in=users_with_conversations
            ).select_related('mentor_profile')[:10]
        elif user.is_mentor:
            # Mentors see their mentees (students who requested mentorship) and other mentors
            from mentorship.models import MentorshipRequest
            mentee_ids = MentorshipRequest.objects.filter(
                mentor=user,
                status__in=['approved', 'in_progress', 'completed']
            ).values_list('student_id', flat=True)

            suggested_users = User.objects.filter(
                Q(id__in=mentee_ids) | Q(role='mentor')
            ).exclude(
                id=user.id
            ).exclude(
                id__in=users_with_conversations
            ).select_related('mentor_profile')[:10]
        else:
            # Admin can message anyone
            suggested_users = User.objects.filter(
                is_active=True
            ).exclude(
                id=user.id
            ).exclude(
                id__in=users_with_conversations
            )[:10]

        context['suggested_users'] = suggested_users

        # Get unread counts and other participant for each conversation
        for conv in context['conversations']:
            conv.unread_count = Message.objects.filter(
                conversation=conv,
                is_read=False
            ).exclude(sender=user).count()
            # Pre-compute the other participant for template use
            conv.other_participant = conv.get_other_participant(user)

        return context


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """View a conversation with messages"""
    template_name = 'chat/conversation.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.messages.select_related('sender')
        context['other_user'] = self.object.get_other_participant(self.request.user)

        # Get all conversations for sidebar
        user = self.request.user
        conversations = Conversation.objects.filter(
            participants=user
        ).prefetch_related('participants', 'messages').annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time', '-updated_at')

        # Add unread counts and other participant for each conversation
        for conv in conversations:
            conv.unread_count = Message.objects.filter(
                conversation=conv,
                is_read=False
            ).exclude(sender=user).count()
            # Pre-compute the other participant for template use
            conv.other_participant = conv.get_other_participant(user)

        context['conversations'] = conversations

        # Mark unread messages as read
        Message.objects.filter(
            conversation=self.object,
            is_read=False
        ).exclude(sender=self.request.user).update(is_read=True, read_at=timezone.now())

        return context


@login_required
def start_conversation(request, user_id):
    """Start or open a conversation with a user"""
    other_user = get_object_or_404(User, pk=user_id)

    if other_user == request.user:
        return redirect('chat:list')

    conversation, created = Conversation.get_or_create_conversation(
        request.user, other_user
    )

    return redirect('chat:conversation', pk=conversation.pk)


@login_required
def send_message(request, conversation_id):
    """Send a message"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    conversation = get_object_or_404(
        Conversation, pk=conversation_id, participants=request.user
    )

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content
    )

    # Notify recipient
    recipient = conversation.get_other_participant(request.user)
    try:
        from notifications.models import Notification
        Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            notification_type='message',
            message=f'New message from {request.user.get_full_name()}'
        )
    except Exception:
        pass

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content,
            'sender': request.user.get_full_name(),
            'created_at': message.created_at.strftime('%H:%M')
        })

    return redirect('chat:conversation', pk=conversation_id)


@login_required
def unread_count(request):
    """Get unread message count"""
    count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()

    return JsonResponse({'count': count})


@login_required
def edit_message(request, message_id):
    """Edit a message"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    message = get_object_or_404(Message, pk=message_id, sender=request.user)

    # Check if message is recent (within 15 minutes)
    time_diff = timezone.now() - message.created_at
    if time_diff.total_seconds() > 900:  # 15 minutes
        return JsonResponse({'error': 'Cannot edit messages older than 15 minutes'}, status=400)

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    message.content = content
    message.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content
        })

    return redirect('chat:conversation', pk=message.conversation_id)


@login_required
def delete_message(request, message_id):
    """Delete a message"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    message = get_object_or_404(Message, pk=message_id, sender=request.user)
    conversation_id = message.conversation_id
    message.delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('chat:conversation', pk=conversation_id)


@login_required
def search_users(request):
    """Search users to start conversation with"""
    query = request.GET.get('q', '').strip()
    user = request.user

    if len(query) < 2:
        return JsonResponse({'users': []})

    # Build base queryset based on user role
    if user.is_student:
        # Students can message mentors
        users = User.objects.filter(
            role='mentor',
            is_active=True
        )
    elif user.is_mentor:
        # Mentors can message students (their mentees) and other mentors
        from mentorship.models import MentorshipRequest
        mentee_ids = MentorshipRequest.objects.filter(
            mentor=user,
            status__in=['approved', 'in_progress', 'completed']
        ).values_list('student_id', flat=True)

        users = User.objects.filter(
            Q(id__in=mentee_ids) | Q(role='mentor')
        )
    else:
        users = User.objects.filter(is_active=True)

    # Filter by search query
    users = users.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=user.id)[:10]

    results = [{
        'id': u.id,
        'name': u.get_full_name(),
        'role': u.get_role_display(),
        'avatar': u.get_avatar_url()
    } for u in users]

    return JsonResponse({'users': results})


