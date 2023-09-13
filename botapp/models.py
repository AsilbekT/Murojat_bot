from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

class TelegramUser(models.Model):
    user_id = models.BigIntegerField(unique=True, verbose_name="Telegram User ID")
    user_lang = models.CharField(max_length=2, null=True, blank=True, choices=[('en', 'English'), ('uz', 'Uzbek'), ('ru', 'Russian')], default='en', verbose_name="User Language")
    fullname = models.CharField(max_length=255, null=True, blank=True, verbose_name="Full Name")
    user_contact = models.CharField(max_length=15, null=True, blank=True, verbose_name="User Contact")
    user_step = models.CharField(max_length=50, null=True, blank=True, verbose_name="User Registration Step")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Updated At")
    is_fully_registered = models.BooleanField(default=False)
    current_message_to_reply = models.BigIntegerField(null=True, blank=True, verbose_name="Current Message to Reply")

    def initiate_conversation(self, admin):
        conversation = Conversation.objects.create(user=self, admin=admin)
        return conversation

    def send_message(self, admin, message_text):
        conversation = Conversation.objects.get_or_create(user=self, admin=admin)[0]
        message = Message.objects.create(conversation=conversation, sender=self, receiver=admin, text=message_text)
        return message

    class Meta:
        verbose_name = "Telegram User"
        verbose_name_plural = "Telegram Users"

    def __str__(self):
        return f"{self.fullname} ({self.user_id})"


class TelegramAdmin(models.Model):
    user = models.OneToOneField(TelegramUser, on_delete=models.CASCADE, verbose_name="User", null=True, blank=True)
    conversations = models.ManyToManyField('TelegramUser', related_name='admin_conversations', blank=True)
    received_messages = GenericRelation('Message', content_type_field='content_type', object_id_field='object_id', related_query_name='telegramadmin')

    class Meta:
        verbose_name = "Telegram Admin"
        verbose_name_plural = "Telegram Admins"

    def __str__(self):
        if self.user and self.user.fullname:
            return f"{self.user.fullname} (Admin)"
        else:
            return "Unlinked Admin"


class Conversation(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    admin = models.ForeignKey(TelegramAdmin, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_messages(self):
        return self.message_set.all().order_by('created_at')


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(TelegramUser, related_name='sent_messages', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    receiver = GenericForeignKey('content_type', 'object_id')
    is_answered = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)


class Content(models.Model):
    category = models.ForeignKey(Category, related_name='contents', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='tutorials/')  # Assuming you have set up media files in your settings
    important_info = models.TextField()