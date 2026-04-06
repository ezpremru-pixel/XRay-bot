from aiohttp import web
import database as db_funcs
from database import Session, User
import logging
import base64
import re
from datetime import datetime, timedelta
from config import config

ADMIN_ID = config.ADMINS[0] if config.ADMINS else 8179216822

async def yookassa_webhook(request):
    data = await request.json()
    bot = request.app['bot']
    try:
        event = data.get('event')
        if event == 'payment.succeeded':
            payment_obj = data.get('object')
            user_id = int(payment_obj.get('metadata').get('user_id'))
            tariff_key = payment_obj.get('metadata').get('tariff')
            amount = payment_obj.get('amount', {}).get('value')
            
            months = 1
            if tariff_key == "2m": months = 2
            elif tariff_key == "3m": months = 3
            elif tariff_key == "6m": months = 6
            elif tariff_key == "12m": months = 12
            elif tariff_key == "test": months = 1
            
            username = "Неизвестно"
            
            with Session() as session:
                user = session.query(User).filter_by(telegram_id=user_id).first()
                if user:
                    username = user.username or user.full_name
                    now = datetime.now()
                    if user.subscription_end and user.subscription_end > now:
                        user.subscription_end += timedelta(days=months * 30)
                    else:
                        user.subscription_end = now + timedelta(days=months * 30)
                    session.commit()
            
            try:
                await bot.send_message(user_id, f"🎉 <b>Оплата прошла успешно!</b>\nПодписка продлена.\n\nНажмите <b>'🚀 ПОДКЛЮЧИТЬ VPN'</b>.", parse_mode='HTML')
            except Exception as e:
                logging.error(f"Ошибка отправки юзеру: {e}")
                
            try:
                await bot.send_message(
                    ADMIN_ID,
                    f"🔔 <b>НОВАЯ ОПЛАТА!</b>\n\n"
                    f"👤 Юзер: @{username} (ID: <code>{user_id}</code>)\n"
                    f"🛒 Тариф: <b>{tariff_key}</b>\n"
                    f"💰 Сумма: <b>{amount} руб.</b>",
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.error(f"Ошибка отправки админу: {e}")

        return web.Response(status=200)
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
        return web.Response(status=400)

async def sub_handler(request):
    user_id = request.match_info.get('user_id')
    try:
        user = await db_funcs.get_user(int(user_id))
        if not user or not user.subscription_end or user.subscription_end < datetime.now():
            return web.Response(text="Subscription expired", status=403)

        keys = user.vless_profile_data 
        if keys:
            # Ищем все ссылки vless://, отсекая HTML-теги вроде </code>
            vless_links = re.findall(r'vless://[^\s<"\'&]+', keys)
            
            # Принудительно меняем названия (всё, что после #)
            if len(vless_links) > 0:
                vless_links[0] = vless_links[0].split('#')[0] + '#🇩🇪_Германия'
            if len(vless_links) > 1:
                vless_links[1] = vless_links[1].split('#')[0] + '#🇨🇭_Швейцария'
                
            clean_keys = "\n".join(vless_links)
            encoded_keys = base64.b64encode(clean_keys.encode('utf-8')).decode('utf-8')
            
            # Магия для приложений: передаем имя подписки через заголовки
            title_base64 = base64.b64encode("⛩ ВОРОТА VPN ⛩".encode('utf-8')).decode('utf-8')
            headers = {
                "profile-title": f"base64:{title_base64}",
                "profile-update-interval": "24"
            }
            return web.Response(text=encoded_keys, headers=headers, content_type='text/plain')
        else:
            return web.Response(text="No keys generated", status=404)
    except Exception as e:
        return web.Response(text="Error", status=500)

def setup_webhook(app, bot):
    app['bot'] = bot
    app.router.add_post('/webhook', yookassa_webhook)
    app.router.add_get('/sub/{user_id}', sub_handler)
