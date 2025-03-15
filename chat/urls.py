from django.urls import path
from .views import StartChatView, SendMessageView, ChatListView, ChatHistoryView

urlpatterns = [
    path('start-chat/', StartChatView.as_view(), name='start_chat'),
    path('send-message/', SendMessageView.as_view(), name='send_message'),
    path('chat-list/', ChatListView.as_view(), name='chat_list'),
    path('chat-history/<int:chat_id>/', ChatHistoryView.as_view(), name='chat_history'),
]
