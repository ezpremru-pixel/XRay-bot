import json
import asyncio
import logging
import warnings
import coloredlogs
from config import config
from aiogram import Bot, Dispatcher
from aiogram.types import PreCheckoutQuery
from handlers import setup_handlers
from datetime import datetime, timedelta
from functions import delete_client_by_email
from database import Session, User, init_db, get_all_users, delete_user_profile

# Импортируем модули для Вебхука ЮKassa и коротких ссылок
from aiohttp import web
from webhook_handler import setup_webhook

warnings.filterwarnings("ignore", category=DeprecationWarning)

coloredlogs.install(level='info')
logger = logging.getLogger(__name__)

# --- Мини-сервер для приема платежей от ЮKassa ---
async def start_web_server(bot: Bot):
    app = web.Application()
    setup_webhook(app, bot) # Передаем бота внутрь вебхука
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 8080)
    await site.start()
    logger.info("✅ Webhook server for Yookassa started on port 8080")

# --- Проверка подписок ---
async def check_subscriptions(bot: Bot):
    while True:
        try:
            now = datetime.utcnow()
            users = await get_all_users()

            for user in users:
                if user.subscription_end - now < timedelta(days=1) and user.subscription_end >= now and not user.notified:
                    try:
                        await bot.send_message(user.telegram_id, "⚠️ Ваша подписка истекает через 24 часа! Продлите доступ.")
                        with Session() as session:
                            db_user = session.query(User).filter_by(telegram_id=user.telegram_id).first()
                            if db_user:
                                db_user.notified = True
                                session.commit()
                    except Exception as e:
                        logger.warning(f"⚠️ Notification error: {e}")

                if user.subscription_end <= now and user.vless_profile_data:
                    try:
                        profile = json.loads(user.vless_profile_data)
                        success = await delete_client_by_email(profile["email"])
                        if success:
                            await delete_user_profile(user.telegram_id)
                            await bot.send_message(user.telegram_id, "❌ Ваша подписка истекла! Профиль VPN удален.")
                        else:
                            logger.warning(f"⚠️ Failed to delete client {profile['email']}")
                    except Exception as e:
                        logger.warning(f"⚠️ Deletion error: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Subscription check error: {e}")
        await asyncio.sleep(3600)

async def update_admins_status():
    with Session() as session:
        session.query(User).update({User.is_admin: False})
        for admin_id in config.ADMINS:
            user = session.query(User).filter_by(telegram_id=admin_id).first()
            if user:
                user.is_admin = True
            else:
                new_admin = User(telegram_id=admin_id, full_name=f"Admin {admin_id}", is_admin=True)
                session.add(new_admin)
        session.commit()
    logger.info("✅ Admin status updated")

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    try:
        await init_db()
        await update_admins_status()
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        return

    try:
        setup_handlers(dp)
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")
        return

    @dp.pre_checkout_query()
    async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    # Запускаем фоновые задачи
    asyncio.create_task(check_subscriptions(bot))
    
    # Запускаем сервер ЮKassa и коротких ссылок
    asyncio.create_task(start_web_server(bot))

    logger.info("ℹ️  Starting bot...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Bot start error: {e}")
        return

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Stopping bot...")
        exit(0)
