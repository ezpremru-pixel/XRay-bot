import os
import logging
from aiohttp import web
from dotenv import load_dotenv

# Подключаем всю нашу логику и роуты из соседнего файла
from webhook_handler import setup_webhook

load_dotenv(override=True)
BOT_TOKEN = os.getenv('BOT_TOKEN')

app = web.Application()

# Подключаем бота, чтобы админка могла слать уведомления (выводы, 2FA)
bot = None
if BOT_TOKEN:
    try:
        from aiogram import Bot
        bot = Bot(token=BOT_TOKEN)
    except ImportError:
        pass

# Передаем управление сервером в webhook_handler
setup_webhook(app, bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print("🚀 Единый WEB-сервер (Подписки + Админка + ЮKassa) запущен на порту 8080...")
    web.run_app(app, host='0.0.0.0', port=8080)
