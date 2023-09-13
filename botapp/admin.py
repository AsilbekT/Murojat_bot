from django.contrib import admin
from .models import Category, Content, TelegramAdmin, TelegramUser, Conversation, Message

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'full_name', 'user_step', 'user_lang', 'user_contact', 'created_at', 'updated_at')
    search_fields = ('user_id', 'full_name', 'user_contact')
    list_filter = ('user_lang', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    def full_name(self, obj):
        return obj.fullname

    full_name.short_description = 'Full Name'


admin.site.register(TelegramAdmin)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Category)
admin.site.register(Content)