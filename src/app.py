import os
import re
import uuid
import asyncio
import logging
import warnings
import coloredlogs
from config import config
from aiogram import Bot, Dispatcher
from aiogram.types import PreCheckoutQuery, FSInputFile
from handlers import setup_handlers
from datetime import datetime, timedelta
from functions import delete_client_by_email
from database import Session, User, init_db, get_all_users, delete_user_profile, PaymentHistory
from yookassa import Payment
import aiohttp

from aiohttp import web
from webhook_handler import setup_webhook

warnings.filterwarnings("ignore", category=DeprecationWarning)
coloredlogs.install(level='info')
logger = logging.getLogger(__name__)

@web.middleware
async def log_request_middleware(request, handler):
    try:
        response = await handler(request)
        return response
    except Exception as e:
        logger.error(f"❌ ОШИБКА ВНУТРИ: {e}")
        raise

async def update_domain(request):
    data = await request.post()
    new_domain = data.get('domain')

    if new_domain:
        new_domain = new_domain.replace("https://", "").replace("http://", "").strip("/")
        env_path = "/root/XRay-bot/.env"

        try:
            with open(env_path, "r", encoding="utf-8") as f:
                env_content = f.read()
        except FileNotFoundError:
            env_content = ""

        if "DOMAIN=" in env_content:
            env_content = re.sub(r"DOMAIN=.*", f"DOMAIN={new_domain}", env_content)
        else:
            env_content += f"\nDOMAIN={new_domain}\n"

        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)

        os.environ["DOMAIN"] = new_domain
        success_html = f"<html><body style='background:#2c2f33; color:white; font-family:sans-serif; padding:30px;'><h2>✅ УСПЕХ!</h2><p>Домен изменен на: <b>{new_domain}</b></p><br><a href='/admin' style='color:#5865F2; text-decoration:none; font-size:18px;'>⬅ Вернуться в админку</a></body></html>"
        return web.Response(text=success_html, content_type='text/html')

    error_html = "<html><body style='background:#2c2f33; color:white; font-family:sans-serif; padding:30px;'><h2>❌ ОШИБКА</h2><p>Вы не ввели домен.</p><br><a href='/admin' style='color:#5865F2; text-decoration:none; font-size:18px;'>⬅ Назад</a></body></html>"
    return web.Response(text=error_html, content_type='text/html', status=400)

async def start_web_server(bot: Bot):
    app = web.Application(middlewares=[log_request_middleware])
    setup_webhook(app, bot)
    app.router.add_post('/admin/update_domain', update_domain)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 8080)
    await site.start()
    logger.info("✅ Web server started")

async def auto_reboot_nodes():
    while True:
        now_utc = datetime.utcnow()
        now_msk = now_utc + timedelta(hours=3)
        next_run_msk = now_msk.replace(hour=4, minute=0, second=0, microsecond=0)
        if now_msk >= next_run_msk:
            next_run_msk += timedelta(days=1)

        sleep_seconds = (next_run_msk - now_msk).total_seconds()
        await asyncio.sleep(sleep_seconds)

        logger.info("🔄 [АВТОРЕБУТ] Запуск ночного сброса Xray (04:00 MSK)...")
        try:
            from functions import SERVERS
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True), connector=connector) as session:
                for srv in SERVERS:
                    try:
                        url = srv['url'].replace("http://", "https://") if "2.27.50.25" in srv['url'] else srv['url']
                        base_url = url.rstrip('/')
                        await session.post(f"{base_url}/login", data={"username": srv['user'], "password": srv['pass']}, timeout=10)
                        await session.post(f"{base_url}/server/restartXrayService", timeout=10)
                        logger.info(f"✅ [АВТОРЕБУТ] Сервер {srv['name']} успешно перезапущен.")
                    except Exception as e:
                        logger.error(f"❌ [АВТОРЕБУТ] Ошибка на {srv['name']}: {e}")
        except Exception as e:
            logger.error(f"❌ [АВТОРЕБУТ] Глоба ошибка: {e}")

async def daily_backup(bot: Bot):
    while True:
        now_utc = datetime.utcnow()
        now_msk = now_utc + timedelta(hours=3)
        next_run_msk = now_msk.replace(hour=3, minute=0, second=0, microsecond=0)
        if now_msk >= next_run_msk:
            next_run_msk += timedelta(days=1)

        sleep_seconds = (next_run_msk - now_msk).total_seconds()
        await asyncio.sleep(sleep_seconds)

        try:
            admin_id = config.ADMINS[0] if config.ADMINS else 8179216822
            backup_file = FSInputFile('users.db')
            await bot.send_document(
                admin_id,
                document=backup_file,
                caption=f"📦 <b>Ежедневный бэкап базы данных</b>\n📅 Дата: {now_msk.strftime('%d.%m.%Y %H:%M')}",
                parse_mode='HTML'
            )
            logger.info("✅ Авто-бэкап базы данных отправлен админу.")
        except Exception as e:
            logger.error(f"❌ Ошибка авто-бэкапа: {e}")

# --- УМНЫЕ РЕКУРРЕНТЫ С ЗАЩИТОЙ ОТ СПАМА ---
# --- УМНЫЕ РЕКУРРЕНТЫ С ЗАЩИТОЙ ОТ СПАМА ---
async def check_subscriptions(bot: Bot):
    while True:
        try:
            now = datetime.now()
            with Session() as session:
                users = session.query(User).filter_by(is_banned=False).all()
                for user in users:
                    # 1. Если нет подписки
                    if not user.subscription_end:
                        if not user.last_reminder or (now - user.last_reminder).total_seconds() > 86400:
                            try:
                                if not user.took_test:
                                    await bot.send_message(user.telegram_id, "👋 <b>Вы еще не пробовали наш VPN?</b>\n\nВам доступен бесплатный тест на 24 часа! Зайдите в меню и нажмите «🎁 ТЕСТ 24ч».", parse_mode='HTML')
                                    user.last_reminder = now
                            except: pass
                        continue

                    delta = user.subscription_end - now
                    is_test = user.took_test and (session.query(PaymentHistory).filter_by(telegram_id=user.telegram_id).count() == 0)

                    # 2. Подписка еще активна
                    if delta.total_seconds() > 0:
                        if is_test:
                            if 39600 < delta.total_seconds() <= 43200 and user.notified_level < 1:
                                try:
                                    await bot.send_message(user.telegram_id, "🚀 <b>Ну как вам скорость?</b>\n\nYouTube и Инста летают? Если есть вопросы — пишите в поддержку!", parse_mode='HTML')
                                    user.notified_level = 1
                                except: pass
                            elif 3600 < delta.total_seconds() <= 7200 and user.notified_level < 2:
                                try:
                                    await bot.send_message(user.telegram_id, "⚠️ <b>Тест заканчивается через 2 часа!</b>\n\nПродлите подписку в разделе 💳 ТАРИФЫ, чтобы интернет оставался свободным.", parse_mode='HTML')
                                    user.notified_level = 2
                                except: pass
                        continue

                    # 3. ПОДПИСКА ЗАКОНЧИЛАСЬ (Считаем точные секунды)
                    expired_seconds = abs(delta.total_seconds())
                    expired_days = expired_seconds / 86400

                    payment_attempted_now = False
                    if user.payment_method_id:
                        if (0 <= expired_days < 1) or (7 <= expired_days < 8) or (14 <= expired_days < 15):
                            if not user.last_reminder or (now - user.last_reminder).total_seconds() > 86400:
                                user.last_reminder = now
                                payment_attempted_now = True
                                
                                # --- ДАЕМ 1 ЧАС БЕЗ ПРЕРЫВАНИЯ СВЯЗИ НА ОБРАБОТКУ ПЛАТЕЖА ---
                                user.subscription_end = now + timedelta(hours=1)
                                # -------------------------------------------------------------

                                try:
                                    p = Payment.create({
                                        "amount": {"value": "149.00", "currency": "RUB"},
                                        "capture": True,
                                        "payment_method_id": user.payment_method_id,
                                        "description": f"Автопродление подписки {user.telegram_id}",
                                        "metadata": {"user_id": user.telegram_id, "tariff": "1m", "type": "sub"},
                                        "receipt": {
                                            "customer": {"email": "info@vorotavpn.ru"},
                                            "items": [{"description": f"VPN Подписка {user.telegram_id}", "amount": {"value": "149.00", "currency": "RUB"}, "vat_code": "1", "quantity": "1.00", "payment_subject": "service", "payment_mode": "full_prepayment"}]
                                        }
                                    }, idempotency_key=str(uuid.uuid4()))

                                    if p.status == 'canceled':
                                        try: await bot.send_message(user.telegram_id, f"❌ <b>Ошибка автопродления!</b>\n\nМы не смогли списать средства с привязанной карты. Доступ к VPN закрыт.\n\nОбновите подписку вручную в разделе 💳 ТАРИФЫ.", parse_mode='HTML')
                                        except: pass
                                except Exception as e:
                                    logger.error(f"❌ Ошибка рекуррента: {e}")
                        elif expired_days >= 21:
                            user.payment_method_id = None
                            try: await bot.send_message(user.telegram_id, "❌ Все попытки автоматического списания исчерпаны. Автопродление отключено, привязанная карта удалена.")
                            except: pass

                    # ЖЕЛЕЗНОЕ ОТКЛЮЧЕНИЕ
                    if user.notified_level != 99:
                        await delete_client_by_email(str(user.telegram_id))
                        user.notified_level = 99
                        if not payment_attempted_now:
                            try: await bot.send_message(user.telegram_id, "❌ <b>Подписка закончилась!</b>\nДоступ к VPN закрыт. Продлите подписку в меню 💳 ТАРИФЫ.", parse_mode='HTML')
                            except: pass

                    # СПАМ НАПОМИНАНИЯ (30 дней)
                    if expired_days <= 30 and not user.payment_method_id and user.notified_level == 99:
                        if not user.last_reminder or (now - user.last_reminder).total_seconds() > 86400:
                            user.last_reminder = now
                            try: await bot.send_message(user.telegram_id, "⚠️ <b>У вас закончилась подписка!</b>\nБез неё доступ к сайтам может быть ограничен. Продлите подписку в 💳 ТАРИФЫ прямо сейчас, чтобы всё снова работало стабильно.", parse_mode='HTML')
                            except: pass

                session.commit()
        except Exception as e:
            logger.error(f"⚠️ Ошибка в check_subscriptions: {e}")
        await asyncio.sleep(60)

async def update_admins_status():
    with Session() as session:
        session.query(User).update({User.is_admin: False})
        for admin_id in config.ADMINS:
            user = session.query(User).filter_by(telegram_id=admin_id).first()
            if user: user.is_admin = True
            else: session.add(User(telegram_id=admin_id, full_name=f"Admin {admin_id}", is_admin=True))
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

    try: setup_handlers(dp)
    except Exception as e:
        logger.error(f"❌ Handler error: {e}")
        return

    @dp.pre_checkout_query()
    async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

    asyncio.create_task(check_subscriptions(bot))
    asyncio.create_task(auto_reboot_nodes())
    asyncio.create_task(daily_backup(bot))
    asyncio.create_task(start_web_server(bot))

    logger.info("ℹ️  Starting bot...")
    try: await dp.start_polling(bot)
    except Exception as e: logger.error(f"❌ Bot start error: {e}")

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: exit(0)
