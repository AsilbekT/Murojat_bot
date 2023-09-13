from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .credentials import BOT_API, URL
from .models import TelegramUser
from .utils import RegistrationHandler, RegisteredUserHandler
import json
import requests

class SetWebhook(View):
    def get(self, request):
        response = requests.post(f"{BOT_API}setWebhook?url={URL}")
        return JsonResponse(response.json())
    
class DeleteWebhook(View):
    def get(self, request):
        response = requests.post(f"{BOT_API}deleteWebhook")
        return JsonResponse(response.json())

@method_decorator(csrf_exempt, name='dispatch')
class Webhook(View):
    def post(self, request):
        data = json.loads(request.body)
        message = data.get('message', {})
        callback_query = data.get('callback_query', {})

        # Get the user info from the message or callback query
        user_info = message.get('from', {}) if message else callback_query.get('from', {})
        user_id = user_info.get('id')
        
        if user_id:
            # Check if the user exists
            user, created = TelegramUser.objects.get_or_create(user_id=user_id)
            
            if callback_query:
                # Handle callback query
                registered_user_handler = RegisteredUserHandler(user)
                registered_user_handler.handle_callback_query(callback_query)
            elif created or (not created and not user.is_fully_registered):
                # Handle the registration
                self.handle_registration(message, user)
            else:
                # Redirect to the main page for registered users
                registered_user_handler = RegisteredUserHandler(user)
                registered_user_handler.process(message.get('text', '').strip())
        
        return JsonResponse({'status': 'ok'})

    def handle_registration(self, message, user):
        text = message.get('text')
        message_data = message.get('contact', {})
        registration_handler = RegistrationHandler(user)
        registration_handler.process(text, message_data)

    def send_message(self, chat_id, text, reply_markup=None):
        data = {
            'chat_id': chat_id,
            'text': text
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        response = requests.post(f"{BOT_API}sendMessage", data)
        return response.json()
