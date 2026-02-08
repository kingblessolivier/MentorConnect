"""
Chat WebSocket Consumer
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat"""
    
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Check if user is authenticated and part of the conversation
        if self.scope['user'].is_anonymous:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_content = data.get('message', '')
        
        if not message_content:
            return
        
        # Save message to database
        message = await self.save_message(message_content)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_content,
                'sender_id': self.scope['user'].id,
                'sender_name': self.scope['user'].get_full_name(),
                'message_id': message.id,
                'timestamp': message.created_at.strftime('%H:%M'),
            }
        )
    
    async def chat_message(self, event):
        """Receive message from room group"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        from .models import Conversation, Message
        
        conversation = Conversation.objects.get(pk=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.scope['user'],
            content=content
        )
        return message
