# credentials.py
from django.conf import settings

BOT_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_API}/"
URL = f"{settings.TELEGRAM_BOT_URL}/webhook/"
