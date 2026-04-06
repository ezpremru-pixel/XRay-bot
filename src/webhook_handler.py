from aiohttp import web
import database as db_funcs
from database import Session, User
import logging
import base64
import re
from datetime import datetime, timedelta
from config import config

ADMIN_ID = config.ADMINS[0] if config.ADMINS else 8179216822

# --- НАСТРОЙКИ АДМИНКИ ---
ADMIN_LOGIN = "admin"
ADMIN_PASS = "vorota2026"  # Можешь поменять на свой

def check_auth(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
    return decoded == f"{ADMIN_LOGIN}:{ADMIN_PASS}"

# --- 1. ОБРАБОТКА ОПЛАТ (ЮKassa) ---
async def yookassa_webhook(request):
    data = await request.json()
    bot = request.app['bot']
    try:
        event = data.get('event')
        if event == 'payment.succeeded':
            payment_obj = data.get('object')
            user_id = int(payment_obj.get('metadata').get('user_id'))
            tariff_key = payment_obj.get('metadata').get('tariff')
            amount = float(payment_obj.get('amount', {}).get('value', 0))
            
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
                    
                    if user.referrer_id:
                        user.subscription_end += timedelta(days=7)
                        ref1 = session.query(User).filter_by(telegram_id=user.referrer_id).first()
                        if ref1:
                            bonus1 = amount * 0.30
                            ref1.balance += bonus1
                            try: await bot.send_message(ref1.telegram_id, f"💸 <b>Вам начислен бонус!</b>\nВаш реферал оплатил VPN. Вы получили: <b>{bonus1:.2f} ₽</b> (30%)", parse_mode='HTML')
                            except: pass
                            
                            if ref1.referrer_id:
                                ref2 = session.query(User).filter_by(telegram_id=ref1.referrer_id).first()
                                if ref2:
                                    bonus2 = amount * 0.05
                                    ref2.balance += bonus2
                                    try: await bot.send_message(ref2.telegram_id, f"💸 <b>Реферальный бонус 2-го уровня!</b>\nВы получили: <b>{bonus2:.2f} ₽</b> (5%)", parse_mode='HTML')
                                    except: pass
                    session.commit()
            
            try: await bot.send_message(user_id, f"🎉 <b>Оплата прошла успешно!</b>\nПодписка продлена.\n\nНажмите <b>'🚀 ПОДКЛЮЧИТЬ VPN'</b>.", parse_mode='HTML')
            except: pass
            try: await bot.send_message(ADMIN_ID, f"🔔 <b>НОВАЯ ОПЛАТА!</b>\n\n👤 Юзер: @{username} (ID: <code>{user_id}</code>)\n🛒 Тариф: <b>{tariff_key}</b>\n💰 Сумма: <b>{amount} руб.</b>", parse_mode='HTML')
            except: pass

        return web.Response(status=200)
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
        return web.Response(status=400)

# --- 2. ВЫДАЧА КЛЮЧЕЙ (/sub/) ---
async def sub_handler(request):
    user_id = request.match_info.get('user_id')
    try:
        user = await db_funcs.get_user(int(user_id))
        if not user or not user.subscription_end or user.subscription_end < datetime.now():
            return web.Response(text="Subscription expired", status=403)

        keys = user.vless_profile_data 
        if keys:
            clean_text = re.sub(r'<[^>]+>', '', keys)
            vless_links = []
            for line in clean_text.split():
                if line.startswith('vless://'):
                    base_link = line.split('#')[0]
                    vless_links.append(base_link)
            
            if len(vless_links) > 0: vless_links[0] += '#🇩🇪_Германия'
            if len(vless_links) > 1: vless_links[1] += '#🇨🇭_Швейцария'
                
            final_keys_str = "\n".join(vless_links)
            encoded_keys = base64.b64encode(final_keys_str.encode('utf-8')).decode('utf-8')
            
            title_base64 = base64.b64encode("⛩ ВОРОТА VPN ⛩".encode('utf-8')).decode('utf-8')
            headers = {"profile-title": f"base64:{title_base64}", "profile-update-interval": "24"}
            return web.Response(text=encoded_keys, headers=headers, content_type='text/plain')
        else:
            return web.Response(text="No keys generated", status=404)
    except:
        return web.Response(text="Error", status=500)

# --- 3. ВЕБ-АДМИНКА (/admin) ---
async def admin_dashboard(request):
    if not check_auth(request):
        return web.Response(status=401, headers={'WWW-Authenticate': 'Basic realm="Admin Area"'}, text="Требуется авторизация")
    
    users = await db_funcs.get_all_users()
    rows = ""
    for u in users:
        sub = u.subscription_end.strftime('%d.%m.%Y %H:%M') if u.subscription_end else '<span style="color:red">Нет</span>'
        rows += f"""
        <tr>
            <td>{u.telegram_id}</td>
            <td>{u.username or u.full_name}</td>
            <td>{sub}</td>
            <td>{u.device_limit}</td>
            <td>{u.balance:.2f} ₽</td>
            <td>
                <a href="/admin/add_days/{u.telegram_id}" class="btn" style="background:#28a745;">+30 Дней</a>
            </td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>VOROTA VPN - Админ Панель</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #1e1e2f; color: #fff; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background: #2a2a40; border-radius: 10px; overflow: hidden; }}
            th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #3d3d5c; }}
            th {{ background: #ff4757; color: white; }}
            tr:hover {{ background: #3d3d5c; }}
            .btn {{ padding: 8px 12px; color: white; text-decoration: none; border-radius: 5px; font-size: 14px; }}
            h1 {{ border-bottom: 2px solid #ff4757; padding-bottom: 10px; display: inline-block; }}
        </style>
    </head>
    <body>
        <h1>⚙️ Управление пользователями</h1>
        <p>Всего пользователей: <b>{len(users)}</b></p>
        <table>
            <tr>
                <th>ID</th>
                <th>Пользователь</th>
                <th>Подписка до</th>
                <th>Лимит устр.</th>
                <th>Баланс</th>
                <th>Действия</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

# --- 4. API АДМИНКИ: ВЫДАТЬ ДНИ ---
async def admin_add_days(request):
    if not check_auth(request): return web.Response(status=401)
    
    user_id = int(request.match_info.get('user_id'))
    await db_funcs.update_subscription(user_id, 1) # Выдаем 1 месяц
    
    # Возвращаем обратно на главную админки
    raise web.HTTPFound('/admin')

def setup_webhook(app, bot):
    app['bot'] = bot
    app.router.add_post('/webhook', yookassa_webhook)
    app.router.add_get('/sub/{user_id}', sub_handler)
    app.router.add_get('/admin', admin_dashboard)
    app.router.add_get('/admin/add_days/{user_id}', admin_add_days)
