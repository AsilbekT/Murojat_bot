from django.urls import path
from .views import SetWebhook, Webhook, DeleteWebhook

urlpatterns = [
    path('setwebhook/', SetWebhook.as_view(), name='set_webhook'),
    path('deletewebhook/', DeleteWebhook.as_view(), name='deletewebhook'),
    path('webhook/', Webhook.as_view(), name='webhook'),
]