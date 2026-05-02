PRIZROKOFFBOT RAILWAY BUILD

Как залить бесплатно на Railway:

1. Создай GitHub репозиторий.
2. Закинь туда эти файлы:
   bot.py
   requirements.txt
   Procfile
   runtime.txt

3. Открой railway.app
4. New Project
5. Deploy from GitHub repo
6. Выбери репозиторий с ботом
7. Открой Variables и добавь:

BOT_TOKEN = токен от BotFather
ADMIN_IDS = твой Telegram ID
LOG_CHAT_ID = можно оставить пустым

8. Deploy.

ВАЖНО:
На Railway НЕ нужен .env файл. Все данные вводятся в Variables.
Если бот до этого запущен на ПК — выключи его, иначе будет ошибка 409.

Команда запуска уже указана в Procfile:
worker: python bot.py
