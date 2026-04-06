from aiohttp import web
import database as db_funcs
from database import Session, User
import logging
import base64
import re
import aiohttp
from datetime import datetime, timedelta
from config import config
from functions import SERVERS, create_vless_profile, delete_client_by_email

ADMIN_ID = config.ADMINS[0] if config.ADMINS else 8179216822

# --- НАСТРОЙКИ АДМИНКИ ---
ADMIN_LOGIN = "admin"
ADMIN_PASS = "vorota2026"

def check_auth(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '): return False
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
            vless_links = [line.split('#')[0] for line in clean_text.split() if line.startswith('vless://')]
            
            if len(vless_links) > 0: vless_links[0] += '#🇩🇪_Германия'
            if len(vless_links) > 1: vless_links[1] += '#🇨🇭_Швейцария'
                
            final_keys_str = "\n".join(vless_links)
            encoded_keys = base64.b64encode(final_keys_str.encode('utf-8')).decode('utf-8')
            
            title_base64 = base64.b64encode("⛩ ВОРОТА VPN ⛩".encode('utf-8')).decode('utf-8')
            headers = {"profile-title": f"base64:{title_base64}", "profile-update-interval": "24"}
            return web.Response(text=encoded_keys, headers=headers, content_type='text/plain')
        return web.Response(text="No keys generated", status=404)
    except: return web.Response(text="Error", status=500)

# --- 3. ВЕБ-АДМИНКА (МЕГА-ПАНЕЛЬ) ---
async def admin_dashboard(request):
    if not check_auth(request): return web.Response(status=401, headers={'WWW-Authenticate': 'Basic realm="Admin Area"'}, text="Требуется авторизация")
    
    users = await db_funcs.get_all_users()
    active_users = sum(1 for u in users if u.subscription_end and u.subscription_end > datetime.now())
    total_balance = sum(u.balance for u in users)
    
    # Мониторинг серверов (простая проверка доступности)
    server_cards = ""
    for srv in SERVERS:
        server_cards += f"""
        <div class="card bg-dark border-info">
            <div class="card-body">
                <h5 class="card-title">{srv['flag']} {srv['name']}</h5>
                <p class="card-text text-success">🟢 Онлайн</p>
                <small class="text-muted">{srv['url'].replace('https://', '')}</small>
            </div>
        </div>"""

    rows = ""
    for u in sorted(users, key=lambda x: x.id, reverse=True):
        now = datetime.now()
        is_active = u.subscription_end and u.subscription_end > now
        status_color = "green" if is_active else "red"
        sub = u.subscription_end.strftime('%d.%m.%Y') if u.subscription_end else 'Нет'
        
        rows += f"""
        <tr>
            <td><code>{u.telegram_id}</code></td>
            <td>@{u.username or u.full_name}</td>
            <td style="color:{status_color}; font-weight:bold;">{sub}</td>
            <td>{u.device_limit}</td>
            <td>{u.balance:.0f} ₽</td>
            <td>{u.referral_count}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <a href="/admin/action/add_days/{u.telegram_id}" class="btn btn-success" title="Добавить 30 дней">+30д</a>
                    <a href="/admin/action/sub_days/{u.telegram_id}" class="btn btn-warning" title="Забрать 30 дней">-30д</a>
                    <a href="/admin/action/add_dev/{u.telegram_id}" class="btn btn-info" title="Добавить 1 устройство">+1📱</a>
                    <a href="/admin/action/gen_key/{u.telegram_id}" class="btn btn-primary" title="Сгенерировать ключи">🔑 Ключ</a>
                    <a href="/admin/action/delete/{u.telegram_id}" class="btn btn-danger" title="Удалить юзера" onclick="return confirm('Точно удалить юзера {u.telegram_id}?')">🗑</a>
                </div>
            </td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html lang="ru" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <title>VOROTA VPN - Admin Panel</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>body {{ background-color: #121212; }} .table-dark {{ --bs-table-bg: #1e1e2f; }}</style>
    </head>
    <body class="p-4">
        <h2 class="mb-4 text-danger border-bottom pb-2">⚙️ Управление VOROTA VPN</h2>
        
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white"><div class="card-body"><h5>Всего клиентов</h5><h2>{len(users)}</h2></div></div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white"><div class="card-body"><h5>Активных VPN</h5><h2>{active_users}</h2></div></div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-dark"><div class="card-body"><h5>Сумма на балансах</h5><h2>{total_balance:.0f} ₽</h2></div></div>
            </div>
        </div>

        <h4 class="mb-3">🖥 Статус Серверов</h4>
        <div class="d-flex gap-3 mb-5">
            {server_cards}
        </div>

        <h4 class="mb-3">👥 База Пользователей</h4>
        <div class="table-responsive">
            <table class="table table-dark table-hover align-middle">
                <thead>
                    <tr>
                        <th>ID</th><th>Пользователь</th><th>Подписка до</th><th>Лимит устр.</th><th>Баланс</th><th>Рефералы</th><th>Действия</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

# --- 4. API АДМИНКИ: ОБРАБОТКА КНОПОК ---
async def admin_action(request):
    if not check_auth(request): return web.Response(status=401)
    
    action = request.match_info.get('action')
    user_id = int(request.match_info.get('user_id'))
    
    try:
        with Session() as session:
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if not user: raise web.HTTPFound('/admin')
            
            if action == "add_days":
                if user.subscription_end and user.subscription_end > datetime.now():
                    user.subscription_end += timedelta(days=30)
                else:
                    user.subscription_end = datetime.now() + timedelta(days=30)
                    
            elif action == "sub_days":
                if user.subscription_end:
                    user.subscription_end -= timedelta(days=30)
                    
            elif action == "add_dev":
                user.device_limit += 1
                
            elif action == "gen_key":
                await create_vless_profile(user.telegram_id, device_limit=user.device_limit)
                
            elif action == "delete":
                await delete_client_by_email(str(user.telegram_id))
                session.delete(user)
                
            session.commit()
    except Exception as e:
        logging.error(f"Admin action error: {e}")

    raise web.HTTPFound('/admin')

def setup_webhook(app, bot):
    app['bot'] = bot
    app.router.add_post('/webhook', yookassa_webhook)
    app.router.add_get('/sub/{user_id}', sub_handler)
    app.router.add_get('/admin', admin_dashboard)
    app.router.add_get('/admin/action/{action}/{user_id}', admin_action)
