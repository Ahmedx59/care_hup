from django.urls import path
from .views import (
    StartChatView,
    SendMessageView,
    ChatListView,
    ChatHistoryView
)

urlpatterns = [
    path('start/', StartChatView.as_view(), name='start-chat'),
    path('send/', SendMessageView.as_view(), name='send-message'),
    path('list/', ChatListView.as_view(), name='chat-list'),
    path('history/<int:chat_id>/', ChatHistoryView.as_view(), name='chat-history'),
]