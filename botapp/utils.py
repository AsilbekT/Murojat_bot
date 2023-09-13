# utils.py
from murojat_website.settings import TELEGRAM_BOT_URL
from .models import Category, Conversation, Message, TelegramAdmin, TelegramUser
from .credentials import BOT_API
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
import requests
import json

class RegistrationHandler:
    steps = [
        'start',
        'get_lang',
        'get_name',
        'get_contact',
    ]
    
    messages = {
        "start": "🌟 Welcome to our bot! Let's get you registered.\n"
                "🌟 Bizning botimizga xush kelibsiz! Keling, sizni ro'yxatdan o'tkazaylik.\n"
                "🌟 Добро пожаловать в наш бот! Давайте зарегистрируем вас.",
                
        "get_lang": "🌐 Please choose your language:\n"
                    "'en' for English 🇬🇧\n"
                    "'uz' for Uzbek 🇺🇿\n"
                    "'ru' for Russian 🇷🇺\n\n"
                    "🌐 Iltimos, tilni tanlang:\n"
                    "'en' inglizcha 🇬🇧\n"
                    "'uz' o'zbekcha 🇺🇿\n"
                    "'ru' ruscha 🇷🇺\n\n"
                    "🌐 Пожалуйста, выберите ваш язык:\n"
                    "'en' для английского 🇬🇧\n"
                    "'uz' для узбекского 🇺🇿\n"
                    "'ru' для русского 🇷🇺",

        "get_name": {
            'en': "📝 Please enter your full name.",
            'uz': "📝 Iltimos, to'liq ismingizni kiriting.",
            'ru': "📝 Пожалуйста, введите свое полное имя."
        },
        
        "get_contact": {
            'en': "📞 Please share your contact number or use the 'Share Contact' button.",
            'uz': "📞 Iltimos, aloqa raqamingizni yozing yoki 'Kontaktni ulashish' tugmasidan foydalaning.",
            'ru': "📞 Пожалуйста, поделитесь своим контактным номером или используйте кнопку 'Поделиться контактом'."
        },
        
        "registered": {
            'en': "✅ Thank you for registering. Redirecting to the main page...",
            'uz': "✅ Ro'yxatdan o'tganiz uchun rahmat. Bosh sahifaga yo'naltirilmoqda...",
            'ru': "✅ Спасибо за регистрацию. Перенаправление на главную страницу..."
        }
    }


    def __init__(self, user):
        self.user = user
        self.current_step = user.user_step or 'start'
        self.current_lang = user.user_lang or 'en'
    
    def process(self, message_text, message_data={}):
        if self.current_step == 'start':
            self._send_message(self.messages['start'])  # Sending the start message
            self._set_next_step()
            self._send_language_buttons()
        elif self.current_step == 'get_lang':
            # Verify if the input matches one of the language codes
            if any(lang_code in message_text for lang_code in ['en', 'uz', 'ru']):
                self.user.user_lang = next(lang_code for lang_code in ['en', 'uz', 'ru'] if lang_code in message_text)
                self.current_lang = self.user.user_lang
                self.user.save()
                self._set_next_step()
                self._send_message(self.messages['get_name'][self.current_lang], remove_keyboard=True)
            else:
                # If input is not a valid language code, send a reminder and show the language options again
                self._send_message("Invalid choice. Please choose a valid language code ('en', 'uz', or 'ru').", remove_keyboard=True)
                self._send_language_buttons()
        elif self.current_step == 'get_name':
            self.user.fullname = message_text
            self._set_next_step()
            self._send_message(self.messages['get_contact'][self.current_lang], request_contact=True)
        elif self.current_step == 'get_contact':
            contact = message_data.get('contact')
            if contact:
                self.user.user_contact = contact['phone_number']
            else:
                self.user.user_contact = message_text
            self.user.user_step = ''
            self.user.is_fully_registered = True
            self.user.save()
            self._send_message(self.messages['registered'][self.current_lang], remove_keyboard=True)
            self.redirect_to_home_page()


    def _set_next_step(self):
        next_step_index = self.steps.index(self.current_step) + 1
        self.current_step = self.steps[next_step_index]
        self.user.user_step = self.current_step
        self.user.save()

    def _send_message(self, message_text, request_contact=False, remove_keyboard=False):
        keyboard = None
        if request_contact:
            keyboard = {
                "keyboard": [[{
                    'text': "Share Contact",
                    'request_contact': True
                }]],
                'resize_keyboard': True
            }
        elif remove_keyboard:
            keyboard = {
                'remove_keyboard': True
            }

        data = {
            'chat_id': self.user.user_id,
            'text': message_text
        }
        
        if keyboard:
            data['reply_markup'] = json.dumps(keyboard)
        
        response = requests.post(f"{BOT_API}sendMessage", data)
        return response.json()
    
    def _send_language_buttons(self):
        keyboard = {
            "keyboard": [
                [{'text': '🇬🇧 English (en)'}, {'text': '🇺🇿 O‘zbekcha (uz)'}, {'text': '🇷🇺 Русский (ru)'}],
            ],
            'resize_keyboard': True,
        }

        data = {
            'chat_id': self.user.user_id,
            'text': ("🌍 *Welcome to our Murojat Bot!* 🤖\n"
                    "👇 Please select your preferred language 👇\n\n"
                    "🌐 *Iltimos, tilingizni tanlang:* 🌐\n"
                    "🌐 *Пожалуйста, выберите ваш язык:* 🌐"),
            'reply_markup': json.dumps(keyboard),
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(f"{BOT_API}sendMessage", data)
        return response.json()

    
    def redirect_to_home_page(self):
        text = {
            'en': "Welcome back! Choose an option:",
            'uz': "Xush kelibsiz! Variantni tanlang:",
            'ru': "Добро пожаловать назад! Выберите вариант:"
        }[self.current_lang]
        
        keyboard = {
            "keyboard": [
                [{"text": self.messages['write_to_admins'][self.current_lang]}],
                [{"text": self.messages['view_categories'][self.current_lang]}],
            ],
            'resize_keyboard': True,
        }
        
        data = {
            'chat_id': self.user.user_id,
            'text': text,
            'reply_markup': json.dumps(keyboard)
        }
        
        response = requests.post(f"{BOT_API}sendMessage", data)
        return response.json()
    

class RegisteredUserHandler:
    command_methods = {
        "write_to_admins": {
            "en": "🖋️ Write to Admins",
            "uz": "🖋️ Administratorlarga yozish",
            "ru": "🖋️ Написать администраторам",
        },
        "received_messages": {
            "en": "❓ Unanswered Questions",
            "uz": "❓ Javob berilmagan savollar",
            "ru": "❓ Вопросы без ответов",
        }, 
        "answered_messages": {
            "en": "Here are the answered messages:",
            "uz": "Javob berilgan xabarlar shu yerda:",
            "ru": "Вот отвеченные сообщения:",
        },
        "view_answered_messages": {
            "en": "✅ Answered Questions",
            "uz": "✅ Javob berilgan savollar",
            "ru": "✅ Ответы на вопросы",
        },
        "view_categories": {
            "en": "📂 View Categories",
            "uz": "📂 Kategoriyalarni ko'rish",
            "ru": "📂 Просмотр категорий",
        },
        "handle_important_things": {
            "en": "handle important things",
            "uz": "muhim ishlarni boshqarish",
            "ru": "управление важными вещами"
        }
    }
    messages = {
        "choose_option": {
            "en": "🎉 Choose an option:",
            "uz": "🎉 Tanlovni tanlang:",
            "ru": "🎉 Выберите опцию:",
        },
        "received_message": {
            "en": "📩 We received your message, we will reply to you as soon as possible.",
            "uz": "📩 Biz sizning xabaringizni qabul qildik, tez orada sizga javob beramiz.",
            "ru": "📩 Мы получили ваше сообщение, мы ответим вам как можно скорее.",
        },
        "no_categories_available": {
            "en": "❌ No categories available.",
            "uz": "❌ Kategoriyalar mavjud emas.",
            "ru": "❌ Категории не доступны.",
        },
        "no_contents_available": {
            "en": "❌ No contents available in the category '{}'.",
            "uz": "❌ '{}' kategoriyasida tarkiblar mavjud emas.",
            "ru": "❌ В категории '{}' нет содержимого.",
        },
        "no_answered_messages": {
            "en": "🚫 No answered messages.",
            "uz": "🚫 Javoblanmagan xabarlar yo'q.",
            "ru": "🚫 Нет ответов на сообщения.",
        },
        "not_an_admin": {
            "en": "⚠️ You are not an admin.",
            "uz": "⚠️ Siz administrator emas siz.",
            "ru": "⚠️ Вы не администратор.",
        },
        "handling_important_things": {
            "en": "⏳ Handling important things...",
            "uz": "⏳ Muhim ishlar bilan shug'ullanmoqda...",
            "ru": "⏳ Работаю над важными вещами...",
        },
        "reply_sent": {
            "en": "✅ Your reply has been sent.",
            "uz": "✅ Sizning javobingiz yuborildi.",
            "ru": "✅ Ваш ответ был отправлен.",
        },
            "contents": {
        "en": "📚 Contents",
        "uz": "📚 Tarkib",
        "ru": "📚 Содержание",
    },
    "title": {
        "en": "🔖 Title",
        "uz": "🔖 Sarlavha",
        "ru": "🔖 Заголовок",
    },
    "description": {
        "en": "📝 Description",
        "uz": "📝 Tavsif",
        "ru": "📝 Описание",
    },
    "important_info": {
        "en": "❗ Important Info",
        "uz": "❗ Muhim Ma'lumot",
        "ru": "❗ Важная Информация",
    },
    "download_resource": {
        "en": "⬇️ Download Resource",
        "uz": "⬇️ Resursni Yuklab Oling",
        "ru": "⬇️ Скачать Ресурс",
    },
    "from": {
        "en": "📩 From",
        "uz": "📩 Kimgan",
        "ru": "📩 От",
    },
    "to": {
        "en": "📤 To",
        "uz": "📤 Kim uchun",
        "ru": "📤 Кому",
    },
    "message": {
        "en": "💬 Message",
        "uz": "💬 Xabar",
        "ru": "💬 Сообщение",
    },
    "status": {
        "en": "🔵 Status",
        "uz": "🔵 Status",
        "ru": "🔵 Статус",
    },
    "no_new_messages": {
        "en": "🚫 No new messages",
        "uz": "🚫 Yangi xabarlar yo'q",
        "ru": "🚫 Нет новых сообщений",
    },
    "replying_to_message_from": {
        "en": "💭 Replying to message from",
        "uz": "💭 Xabarga javob berish",
        "ru": "💭 Ответ на сообщение от",
    },
    "please_type_your_reply": {
        "en": "📥 Please type your reply",
        "uz": "📥 Iltimos, javobingizni kiriting",
        "ru": "📥 Пожалуйста, введите ваш ответ",
    },
    "write_to_admins": {
        "en": "🖋️ Write to Admins",
        "uz": "🖋️ Administratorlarga yozish",
        "ru": "🖋️ Написать администраторам",
    },
    "unanswered_questions": {
        "en": "❓ Unanswered Questions",
        "uz": "❓ Javob berilmagan savollar",
        "ru": "❓ Вопросы без ответов",
    },
    "answered_questions": {
        "en": "✅ Answered Questions",
        "uz": "✅ Javob berilgan savollar",
        "ru": "✅ Ответы на вопросы",
    },
    "view_categories": {
        "en": "📂 View Categories",
        "uz": "📂 Kategoriyalarni ko'rish",
        "ru": "📂 Просмотр категорий",
    },
    "handle_important_things": {
        "en": "🔍 Handle Important Things",
        "uz": "🔍 Muhim ishlarni boshqarish",
        "ru": "🔍 Управление важными вещами",
    },
    "enter_user_id": {
        "en": "🆔 Please enter the user ID",
        "uz": "🆔 Iltimos, foydalanuvchi ID-sini kiriting",
        "ru": "🆔 Пожалуйста, введите ID пользователя",
    },
    "type_message_to_admins": {
        "en": "📝 Please type your message to the admins",
        "uz": "📝 Iltimos, administratorlarga xabaringizni yozing",
        "ru": "📝 Пожалуйста, напишите ваше сообщение администраторам",
    },
    "type_your_message": {
        "en": "✍️ Please type your message",
        "uz": "✍️ Iltimos, xabaringizni yozing",
        "ru": "✍️ Пожалуйста, напишите ваше сообщение",
    },
    "select_category_to_view_contents": {
        "en": "🔍 Please select a category to view its contents",
        "uz": "🔍 Iltimos, tarkibini ko'rish uchun kategoriyani tanlang",
        "ru": "🔍 Пожалуйста, выберите категорию для просмотра ее содержимого",
    },
    "answer_to_this": {
        "en": "💬 Answer to this",
        "uz": "💬 Bunga javob bering",
        "ru": "💬 Ответить на это",
    },
            "reply_from": {
            "en": "🔙 Reply from",
            "uz": "🔙 Javob shaklida",
            "ru": "🔙 Ответ от",
        },
        "admin_does_not_exist": {
            "en": "⚠️ The admin does not exist!",
            "uz": "⚠️ Administrator mavjud emas!",
            "ru": "⚠️ Администратор не существует!",
        },
        "choose_option": {
            "en": "👇 Choose an option:",
            "uz": "👇 Tanlovni tanlang:",
            "ru": "👇 Выберите опцию:",
        },
        "received_message": {
            "en": "✉️ We received your message, we will reply to you as soon as possible.",
            "uz": "✉️ Biz sizning xabaringizni qabul qildik, tez orada sizga javob beramiz.",
            "ru": "✉️ Мы получили ваше сообщение, мы ответим вам как можно скорее.",
        },
        "no_categories_available": {
            "en": "⚠️ No categories available.",
            "uz": "⚠️ Kategoriyalar mavjud emas.",
            "ru": "⚠️ Категории не доступны.",
        },
        "no_contents_available": {
            "en": "⚠️ No contents available in the category '{}'.",
            "uz": "⚠️ '{}' kategoriyasida tarkiblar mavjud emas.",
            "ru": "⚠️ В категории '{}' нет содержимого.",
        },
        "no_answered_messages": {
            "en": "🚫 No answered messages.",
            "uz": "🚫 Javob berilmagan xabarlar yo'q.",
            "ru": "🚫 Нет ответов на сообщения.",
        },
        "not_an_admin": {
            "en": "⛔ You are not an admin.",
            "uz": "⛔ Siz administrator emas siz.",
            "ru": "⛔ Вы не администратор.",
        },
        "handling_important_things": {
            "en": "⚙️ Handling important things...",
            "uz": "⚙️ Muhim ishlar bilan shug'ullanmoqda...",
            "ru": "⚙️ Работаю над важными вещами...",
        },
        "reply_sent": {
            "en": "✉️ Your reply has been sent.",
            "uz": "✉️ Sizning javobingiz yuborildi.",
            "ru": "✉️ Ваш ответ был отправлен.",
        }
    }


    def __init__(self, user):
        self.user = user
        self.current_lang = user.user_lang or 'uz'

    def process(self, message_text):
        print(message_text)
        if self.user.user_step == 'waiting_for_user_id':
            self.handle_user_id_input(message_text)
        elif self.user.user_step == 'waiting_for_message_to_admin':
            self.handle_message_to_admin_input(message_text)
        else:
            for command, translations in self.command_methods.items():
                if message_text.lower() == translations.get(self.current_lang, "").lower():
                    getattr(self, command.replace(" ", "_"))()
                    break
            else:
                if self.user.user_step == 'replying_to_message':
                    self.handle_reply_to_message(message_text)
                else:
                    self.show_options()


    def show_options(self):
        is_admin = TelegramAdmin.objects.filter(user=self.user).exists()
        if is_admin:
            keyboard = {
                "keyboard": [
                    [self.messages.get("view_categories", {}).get(self.current_lang, "View Categories"), self.messages.get("unanswered_questions", {}).get(self.current_lang, "Unanswered Questions")],
                    [self.messages.get("answered_questions", {}).get(self.current_lang, "Answered Questions")],
                ],
                'resize_keyboard': True,
            }
        else:
            keyboard = {
                "keyboard": [
                    [self.messages.get("write_to_admins", {}).get(self.current_lang, "Write to Admins")],
                    [self.messages.get("view_categories", {}).get(self.current_lang, "View Categories")],
                ],
                'resize_keyboard': True,
            }

        message_text = self.messages.get("choose_option", {}).get(self.current_lang, "Choose an Option")
        
        self._send_message(message_text, keyboard)

    def write_to_admins(self):
        user_id = self.user.user_id
        is_admin = TelegramAdmin.objects.filter(user=self.user).exists()
        if is_admin:
            self._send_message(self.messages["enter_user_id"][self.current_lang])
            self.user.user_step = 'waiting_for_user_id'
        else:
            self._send_message(self.messages["type_message_to_admins"][self.current_lang])
            self.user.user_step = 'waiting_for_message_to_admin'
        self.user.save()

    def handle_message_to_admin_input(self, message_input):
        if self.user.user_step == 'waiting_for_message_to_admin':
            admin_ids = TelegramAdmin.objects.values_list('user__user_id', flat=True)
            for admin_id in admin_ids:
                admin = TelegramAdmin.objects.get(user__user_id=admin_id)
                saved_message = self.user.send_message(admin, message_input)
            self.user.user_step = ''
            self.user.save()
            self._send_message(self.messages["received_message"][self.current_lang])

    def handle_user_id_input(self, user_id_input):
        # Validate and process the user ID input.
        # Implement the validation logic as required.
        self.user.recipient_user_id = user_id_input
        self.user.user_step = 'waiting_for_message'
        self.user.save()
        self._send_message(self.messages["type_your_message"][self.current_lang])

    def view_categories(self):
        categories = Category.objects.all()
        if categories:
            keyboard = {
                "inline_keyboard": [[{"text": category.name, "callback_data": json.dumps({"action": "view_category_contents", "category_id": category.id})}] for category in categories]
            }

            data = {
                'chat_id': self.user.user_id,
                'text': self.messages["select_category_to_view_contents"][self.current_lang],
                'reply_markup': json.dumps(keyboard)
            }

            response = requests.post(f"{BOT_API}sendMessage", data)
            return response.json()
        else:
            self._send_message(self.messages["no_categories_available"][self.current_lang])

    def view_category_contents(self, category_id, message_id):
        category = Category.objects.get(id=category_id)
        contents = category.contents.all()
        if contents:
            text = f"*{category.name} {self.messages['contents'][self.current_lang]}:*\n\n"
            for content in contents:
                text += f"• *{self.messages['title'][self.current_lang]}:* {content.title}\n"
                text += f"• *{self.messages['description'][self.current_lang]}:* {content.description}\n"
                text += f"• *{self.messages['important_info'][self.current_lang]}:* {content.important_info}\n"
                text += f"[{self.messages['download_resource'][self.current_lang]}]({TELEGRAM_BOT_URL + content.file.url})\n\n"

            # Now edit the message with the new text
            data = {
                'chat_id': self.user.user_id,
                'message_id': message_id,
                'text': text,
                'parse_mode': 'Markdown'

            }

            response = requests.post(f"{BOT_API}editMessageText", data)
            return response.json()
        else:
            data = {
                'chat_id': self.user.user_id,
                'message_id': message_id,  # the message ID of the message to be edited
                'text': f"{self.messages['no_contents_available'][self.current_lang]} '{category.name}'.", 
            }

            response = requests.post(f"{BOT_API}editMessageText", data)
            return response.json()

    def view_answered_messages(self):
        user_id = self.user.user_id
        try:
            admin_instance = TelegramAdmin.objects.get(user__user_id=user_id)
            answered_messages = admin_instance.received_messages.filter(is_answered=True).order_by('-created_at')
        except TelegramAdmin.DoesNotExist:
            self._send_message(self.messages["not_an_admin"][self.current_lang])
            return

        if answered_messages:
            self._send_message(self.command_methods["view_answered_messages"][self.current_lang])
            for message in answered_messages:
                text = f"{self.messages['from'][self.current_lang]}: {message.sender.fullname} ({message.sender.user_id})\n{self.messages['to'][self.current_lang]}: {message.receiver.user.fullname} ({message.receiver.user.user_id})\n{self.messages['message'][self.current_lang]}: {message.text}\n{self.messages['status'][self.current_lang]}: ✅"
                data = {
                    'chat_id': user_id,
                    'text': text,
                }
                response = requests.post(f"{BOT_API}sendMessage", data)
        else:
            self._send_message(self.messages["no_answered_messages"][self.current_lang])

    def received_messages(self):
        user_id = self.user.user_id
        try:
            admin_instance = TelegramAdmin.objects.get(user__user_id=user_id)
            messages = admin_instance.received_messages.filter(is_answered=False).order_by('-created_at')
        except TelegramAdmin.DoesNotExist:
            self._send_message(self.messages["not_an_admin"][self.current_lang])
            return

        if messages:
            for message in messages:
                text = f"{self.messages['from'][self.current_lang]}: {message.sender.fullname} ({message.sender.user_id})\n{self.messages['message'][self.current_lang]}: {message.text}"
                inline_keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": self.messages["answer_to_this"][self.current_lang],
                                "callback_data": json.dumps({"action": "reply", "message_id": message.id})
                            }
                        ]
                    ]
                }
                data = {
                    'chat_id': user_id,
                    'text': text,
                    'reply_markup': json.dumps(inline_keyboard)
                }
                response = requests.post(f"{BOT_API}sendMessage", data)
        else:
            self._send_message(self.messages["no_new_messages"][self.current_lang])

    def handle_callback_query(self, callback_query):
        data = json.loads(callback_query['data'])
        if 'message_id' in data:  # checking if 'message_id' is in the data dictionary
            message_id = data['message_id']
        else:
            message_id = callback_query['message']['message_id']  # getting the message ID from the callback query
        if data['action'] == 'reply':
            message = Message.objects.get(id=message_id)  # Now message_id is correctly defined
            self.user.user_step = 'replying_to_message'
            self.user.current_message_to_reply = message_id  # Storing the message_id to refer to later
            self.user.save()
            self._send_message(f"{self.messages['replying_to_message_from'][self.current_lang]} {message.sender.fullname}. {self.messages['please_type_your_reply'][self.current_lang]}")
        elif data['action'] == 'view_category_contents':
            self.view_category_contents(data['category_id'], message_id)

    def handle_important_things(self):
        # Your logic to handle "important things" goes here.
        self._send_message(self.messages["handling_important_things"][self.current_lang])

    def _send_message(self, message_text, inline_keyboard=None):
        data = {
            'chat_id': self.user.user_id,
            'text': message_text
        }

        if inline_keyboard:
            data['reply_markup'] = json.dumps(inline_keyboard)

        response = requests.post(f"{BOT_API}sendMessage", data)
        return response.json()

    def handle_reply_to_message(self, reply_text):
        message_to_reply = Message.objects.get(id=self.user.current_message_to_reply)
        try:
            # Get the TelegramUser instance linked to the admin who is the receiver of the message_to_reply
            admin_instance = TelegramAdmin.objects.get(user=message_to_reply.receiver.user)
            user_instance = admin_instance.user  # Get the TelegramUser instance
            new_message = Message(
                conversation=message_to_reply.conversation,
                sender=user_instance,  # Now it's a TelegramUser instance
                text=reply_text,
                content_type=ContentType.objects.get_for_model(TelegramUser),
                object_id=message_to_reply.sender.id
            )
            new_message.save()
        except ObjectDoesNotExist:
            self._send_message(self.messages["admin_does_not_exist"][self.current_lang])
            return

        data = {
            'chat_id': message_to_reply.sender.user_id,
            'text': f"{self.messages['reply_from'][self.current_lang]} {self.user.fullname}: {reply_text}"
        }

        response = requests.post(f"{BOT_API}sendMessage", data)
        response.json()
        message_to_reply.is_answered = True
        message_to_reply.save()

        self.user.user_step = ''
        self.user.current_message_to_reply = None
        self.user.save()

        self._send_message(self.messages["reply_sent"][self.current_lang])
