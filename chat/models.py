"""
Chat App Models
Real-time chat between users using Django Channels
"""

from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """
    Conversation between two users
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        names = [p.get_full_name() for p in self.participants.all()[:2]]
        return f"Conversation: {' & '.join(names)}"

    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=user.id).first()

    def get_last_message(self):
        """Get the most recent message"""
        return self.messages.order_by('-created_at').first()

    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get or create a conversation between two users"""
        conversations = cls.objects.filter(participants=user1).filter(participants=user2)
        if conversations.exists():
            return conversations.first(), False
        conversation = cls.objects.create()
        conversation.participants.add(user1, user2)
        return conversation, True


class Message(models.Model):
    """
    Message in a conversation
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.get_full_name()}: {self.content[:50]}..."

    def mark_as_read(self):
        """Mark message as read"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update conversation's updated_at
        self.conversation.save()
