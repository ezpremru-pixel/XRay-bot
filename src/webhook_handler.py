from aiohttp import web
import database as db_funcs
from database import Session, User
import logging
import base64
import re
import aiohttp
import json
from datetime import datetime, timedelta
from config import config
from functions import SERVERS, create_vless_profile, delete_client_by_email

ADMIN_ID = config.ADMINS[0] if config.ADMINS else 8179216822

ADMIN_LOGIN = "admin"
ADMIN_PASS = "vorota2026"

def check_auth(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '): return False
    decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
    return decoded == f"{ADMIN_LOGIN}:{ADMIN_PASS}"

# --- РЕАЛЬНЫЙ СТАТУС СЕРВЕРОВ ИЗ X-UI ---
async def get_real_server_stats():
    stats = []
    for srv in SERVERS:
        srv_data = {"name": srv['name'], "flag": srv['flag'], "url": srv['url'], "status": "🔴 Оффлайн", "cpu": "0%", "ram": "0%", "uptime": "-"}
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
                login_resp = await session.post(f"{srv['url']}/login", data={"username": srv['user'], "password": srv['pass']}, timeout=3)
                if login_resp.status == 200:
                    status_resp = await session.post(f"{srv['url']}/server/status", timeout=3)
                    if status_resp.status == 200:
                        data = await status_resp.json()
                        obj = data.get("obj", {})
                        srv_data["status"] = "🟢 Онлайн"
                        srv_data["cpu"] = f"{obj.get('cpu', 0)}%"
                        srv_data["ram"] = f"{obj.get('mem', {}).get('current', 0) // 1024 // 1024} MB"
                        srv_data["uptime"] = f"{obj.get('uptime', 0) // 86400} дн."
        except Exception as e:
            pass
        stats.append(srv_data)
    return stats

# --- 1. ОБРАБОТКА ОПЛАТ ---
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
                            try: await bot.send_message(ref1.telegram_id, f"💸 <b>Вам начислен бонус!</b>\nРеферал оплатил VPN. Вы получили: <b>{bonus1:.2f} ₽</b> (30%)", parse_mode='HTML')
                            except: pass
                            
                            if ref1.referrer_id:
                                ref2 = session.query(User).filter_by(telegram_id=ref1.referrer_id).first()
                                if ref2:
                                    bonus2 = amount * 0.05
                                    ref2.balance += bonus2
                                    try: await bot.send_message(ref2.telegram_id, f"💸 <b>Бонус 2-го уровня!</b>\nВы получили: <b>{bonus2:.2f} ₽</b> (5%)", parse_mode='HTML')
                                    except: pass
                    session.commit()
            
            try: await bot.send_message(user_id, f"🎉 <b>Оплата прошла успешно!</b>\nПодписка продлена.\n\nНажмите <b>'🚀 ПОДКЛЮЧИТЬ VPN'</b>.", parse_mode='HTML')
            except: pass
            try: await bot.send_message(ADMIN_ID, f"🔔 <b>НОВАЯ ОПЛАТА!</b>\n\n👤 Юзер: @{username} (ID: <code>{user_id}</code>)\n🛒 Тариф: <b>{tariff_key}</b>\n💰 Сумма: <b>{amount} руб.</b>", parse_mode='HTML')
            except: pass

        return web.Response(status=200)
    except: return web.Response(status=400)

# --- 2. ВЫДАЧА КЛЮЧЕЙ (/sub/) ---
async def sub_handler(request):
    user_id = request.match_info.get('user_id')
    try:
        user = await db_funcs.get_user(int(user_id))
        if not user or not user.subscription_end or user.subscription_end < datetime.now(): return web.Response(text="Subscription expired", status=403)
        keys = user.vless_profile_data 
        if keys:
            vless_raw = re.findall(r'(vless://[^\s<>"\']+)', keys)
            cleaned = [link.split('#')[0] for link in vless_raw]
            if len(cleaned) > 0: cleaned[0] += '#🇩🇪_Германия'
            if len(cleaned) > 1: cleaned[1] += '#🇨🇭_Швейцария'
            encoded_keys = base64.b64encode("\n".join(cleaned).encode('utf-8')).decode('utf-8')
            return web.Response(text=encoded_keys, headers={"profile-title": f"base64:{base64.b64encode('⛩ ВОРОТА VPN ⛩'.encode('utf-8')).decode('utf-8')}", "profile-update-interval": "24"}, content_type='text/plain')
        return web.Response(text="No keys generated", status=404)
    except: return web.Response(text="Error", status=500)

# --- 3. МЕГА ВЕБ-АДМИНКА ---
async def admin_dashboard(request):
    if not check_auth(request): return web.Response(status=401, headers={'WWW-Authenticate': 'Basic realm="Admin Area"'}, text="Auth required")
    
    users = await db_funcs.get_all_users()
    active_users = sum(1 for u in users if u.subscription_end and u.subscription_end > datetime.now())
    
    # Таблица юзеров
    user_rows = ""
    ref_rows = ""
    for u in sorted(users, key=lambda x: x.id, reverse=True):
        is_active = u.subscription_end and u.subscription_end > datetime.now()
        sub = u.subscription_end.strftime('%d.%m.%Y') if u.subscription_end else 'Нет'
        color = "text-success" if is_active else "text-danger"
        
        # Пользователи
        user_rows += f"""
        <tr>
            <td><code>{u.telegram_id}</code></td>
            <td>@{u.username or u.full_name}</td>
            <td class="{color} fw-bold">{sub}</td>
            <td>{u.device_limit}</td>
            <td>
                <form action="/admin/action/custom_days/{u.telegram_id}" method="POST" class="d-flex gap-1">
                    <input type="number" name="days" class="form-control form-control-sm bg-dark text-white border-secondary" placeholder="± Дни" style="width: 70px;" required>
                    <button type="submit" class="btn btn-sm btn-outline-success">OK</button>
                </form>
            </td>
            <td>
                <a href="/admin/action/add_dev/{u.telegram_id}" class="btn btn-sm btn-info" title="Добавить 1 устройство">+1📱</a>
                <a href="/admin/action/gen_key/{u.telegram_id}" class="btn btn-sm btn-primary" title="Сгенерировать ключи">🔑</a>
                <a href="/admin/action/delete/{u.telegram_id}" class="btn btn-sm btn-danger" onclick="return confirm('Удалить?')">🗑</a>
            </td>
        </tr>"""
        
        # Рефералка
        if u.referral_count > 0 or u.balance > 0:
            ref_rows += f"""
            <tr>
                <td><code>{u.telegram_id}</code></td>
                <td>@{u.username or u.full_name}</td>
                <td><span class="badge bg-primary fs-6">{u.referral_count} чел.</span></td>
                <td><span class="badge bg-success fs-6">{u.balance:.2f} ₽</span></td>
                <td>{"<code>" + str(u.referrer_id) + "</code>" if u.referrer_id else "-"}</td>
            </tr>"""

    # Мониторинг серверов
    srv_stats = await get_real_server_stats()
    srv_cards = ""
    for s in srv_stats:
        status_badge = "bg-success" if "Онлайн" in s['status'] else "bg-danger"
        srv_cards += f"""
        <div class="col-md-6 mb-3">
            <div class="card bg-dark border-secondary">
                <div class="card-body">
                    <h5 class="card-title">{s['flag']} {s['name']} <span class="badge {status_badge} float-end">{s['status']}</span></h5>
                    <p class="mb-1 text-muted small">{s['url']}</p>
                    <div class="d-flex justify-content-between mt-3">
                        <div><small>CPU:</small> <span class="text-warning fw-bold">{s['cpu']}</span></div>
                        <div><small>RAM:</small> <span class="text-info fw-bold">{s['ram']}</span></div>
                        <div><small>Uptime:</small> <span class="text-light fw-bold">{s['uptime']}</span></div>
                    </div>
                </div>
            </div>
        </div>"""

    html = f"""
    <!DOCTYPE html>
    <html lang="ru" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <title>VOROTA VPN - CRM</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <style>body {{ background-color: #0d1117; }} .nav-tabs .nav-link {{ color: #c9d1d9; }} .nav-tabs .nav-link.active {{ background-color: #161b22; border-color: #30363d #30363d transparent; color: #58a6ff; font-weight:bold; }} .table-dark {{ --bs-table-bg: #161b22; }}</style>
    </head>
    <body class="p-4">
        <h2 class="mb-4 text-primary border-bottom border-secondary pb-2">⛩ VOROTA VPN | Admin Control</h2>
        
        <ul class="nav nav-tabs mb-4" id="adminTabs" role="tablist">
            <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#users">👥 Пользователи ({len(users)})</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#refs">🤝 Рефералы</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#servers">🖥 Мониторинг</button></li>
        </ul>

        <div class="tab-content">
            <div class="tab-pane fade show active" id="users">
                <div class="table-responsive">
                    <table class="table table-dark table-hover table-bordered border-secondary align-middle text-center">
                        <thead class="table-active"><tr><th>ID</th><th>Ник</th><th>Подписка</th><th>Лимит 📱</th><th>Изменить дни</th><th>Действия</th></tr></thead>
                        <tbody>{user_rows}</tbody>
                    </table>
                </div>
            </div>

            <div class="tab-pane fade" id="refs">
                <div class="table-responsive">
                    <table class="table table-dark table-hover table-bordered border-secondary align-middle text-center">
                        <thead class="table-active"><tr><th>ID</th><th>Ник</th><th>Пригласил</th><th>Баланс</th><th>Чей он реферал (ID)</th></tr></thead>
                        <tbody>{ref_rows}</tbody>
                    </table>
                </div>
            </div>

            <div class="tab-pane fade" id="servers">
                <div class="row">{srv_cards}</div>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

# --- 4. API: ОБРАБОТКА ДЕЙСТВИЙ И УВЕДОМЛЕНИЯ ---
async def admin_action(request):
    if not check_auth(request): return web.Response(status=401)
    
    action = request.match_info.get('action')
    user_id = int(request.match_info.get('user_id'))
    bot = request.app['bot']
    
    try:
        with Session() as session:
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if not user: raise web.HTTPFound('/admin')
            
            # --- ВВОД ЛЮБОГО КОЛ-ВА ДНЕЙ ---
            if action == "custom_days":
                data = await request.post()
                days = int(data.get('days', 0))
                if days != 0:
                    if user.subscription_end and user.subscription_end > datetime.now():
                        user.subscription_end += timedelta(days=days)
                    else:
                        user.subscription_end = datetime.now() + timedelta(days=days)
                    
                    word = "добавил" if days > 0 else "убавил"
                    try: await bot.send_message(user_id, f"👨‍💻 <b>Уведомление от Администратора:</b>\nВам {word} <b>{abs(days)} дней</b> подписки.\nТекущая дата окончания: {user.subscription_end.strftime('%d.%m.%Y')}", parse_mode='HTML')
                    except: pass
                    
            # --- УВЕЛИЧЕНИЕ ЛИМИТА ---
            elif action == "add_dev":
                user.device_limit += 1
                try: await bot.send_message(user_id, f"📱 <b>Уведомление:</b>\nВаш лимит устройств увеличен!\nТеперь вам доступно: <b>{user.device_limit} шт.</b>", parse_mode='HTML')
                except: pass
                # Пересоздаем ключи, чтобы лимит применился в X-UI
                await create_vless_profile(user.telegram_id, device_limit=user.device_limit)
                
            # --- ГЕНЕРАЦИЯ КЛЮЧА ---
            elif action == "gen_key":
                await create_vless_profile(user.telegram_id, device_limit=user.device_limit)
                try: await bot.send_message(user_id, f"🔑 <b>Внимание:</b>\nАдминистратор принудительно обновил ваши ключи доступа.\nПожалуйста, зайдите в приложение и обновите подписку.", parse_mode='HTML')
                except: pass
                
            # --- УДАЛЕНИЕ ---
            elif action == "delete":
                await delete_client_by_email(str(user.telegram_id))
                try: await bot.send_message(user_id, f"❌ Ваш аккаунт VPN был удален администратором.", parse_mode='HTML')
                except: pass
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
    app.router.add_post('/admin/action/{action}/{user_id}', admin_action) # Для формы с днями
    app.router.add_get('/admin/action/{action}/{user_id}', admin_action) # Для остальных кнопок
