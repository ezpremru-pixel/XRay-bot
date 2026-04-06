from aiohttp import web
import database as db_funcs
from database import Session, User, PaymentHistory
import logging
import base64
import re
import aiohttp
from datetime import datetime, timedelta
from config import config
from functions import SERVERS, create_vless_profile, delete_client_by_email

ADMIN_ID = config.ADMINS[0] if config.ADMINS else 8179216822
ADMIN_LOGIN, ADMIN_PASS = "admin", "vorota2026"

def check_auth(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '): return False
    return base64.b64decode(auth_header[6:]).decode('utf-8') == f"{ADMIN_LOGIN}:{ADMIN_PASS}"

async def get_real_server_stats():
    stats = []
    # ОТКЛЮЧАЕМ ПРОВЕРКУ SSL ДЛЯ ПАНЕЛИ
    connector = aiohttp.TCPConnector(ssl=False)
    for srv in SERVERS:
        srv_data = {"name": srv['name'], "flag": srv['flag'], "url": srv['url'], "status": "🔴 Оффлайн", "cpu": "0%", "ram": "0%", "uptime": "-"}
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                login_resp = await session.post(f"{srv['url']}/login", data={"username": srv['user'], "password": srv['pass']}, timeout=5)
                if login_resp.status == 200:
                    status_resp = await session.post(f"{srv['url']}/server/status", timeout=5)
                    if status_resp.status == 200:
                        data = await status_resp.json()
                        obj = data.get("obj", {})
                        srv_data["status"] = "🟢 Онлайн"
                        srv_data["cpu"] = f"{obj.get('cpu', 0)}%"
                        srv_data["ram"] = f"{obj.get('mem', {}).get('current', 0) // 1024 // 1024} MB"
                        srv_data["uptime"] = f"{obj.get('uptime', 0) // 86400} дн."
        except: pass
        stats.append(srv_data)
    return stats

async def yookassa_webhook(request):
    data = await request.json()
    bot = request.app['bot']
    try:
        if data.get('event') == 'payment.succeeded':
            payment_obj = data.get('object')
            user_id = int(payment_obj.get('metadata').get('user_id'))
            tariff_key = payment_obj.get('metadata').get('tariff')
            amount = float(payment_obj.get('amount', {}).get('value', 0))
            is_device = payment_obj.get('metadata').get('type') == 'device'
            
            with Session() as session:
                user = session.query(User).filter_by(telegram_id=user_id).first()
                if user:
                    # Запись в историю платежей
                    action_desc = f"Покупка VPN ({tariff_key})" if not is_device else f"Доп. устройство"
                    rec = PaymentHistory(telegram_id=user_id, amount=amount, action=action_desc)
                    session.add(rec)

                    now = datetime.now()
                    if is_device:
                        dev_count = int(tariff_key.split('_')[1]) if '_' in tariff_key else 1
                        user.extra_device_limit += dev_count
                        user.extra_device_end = now + timedelta(days=30)
                    else:
                        months = 1
                        if tariff_key == "2m": months = 2
                        elif tariff_key == "3m": months = 3
                        elif tariff_key == "6m": months = 6
                        elif tariff_key == "12m": months = 12
                        
                        if user.subscription_end and user.subscription_end > now:
                            user.subscription_end += timedelta(days=months * 30)
                        else:
                            user.subscription_end = now + timedelta(days=months * 30)
                            
                        # Рефералка (начисление)
                        if user.referrer_id:
                            user.subscription_end += timedelta(days=7)
                            ref1 = session.query(User).filter_by(telegram_id=user.referrer_id).first()
                            if ref1:
                                ref1.balance += amount * 0.30
                                if ref1.referrer_id:
                                    ref2 = session.query(User).filter_by(telegram_id=ref1.referrer_id).first()
                                    if ref2: ref2.balance += amount * 0.05
                    session.commit()
        return web.Response(status=200)
    except: return web.Response(status=400)

async def sub_handler(request):
    user_id = request.match_info.get('user_id')
    try:
        user = await db_funcs.get_user(int(user_id))
        if not user or not user.subscription_end or user.subscription_end < datetime.now(): return web.Response(text="Expired", status=403)
        if user.vless_profile_data:
            vless_raw = re.findall(r'(vless://[^\s<>"\']+)', user.vless_profile_data)
            cleaned = [link.split('#')[0] for link in vless_raw]
            if len(cleaned) > 0: cleaned[0] += '#🇩🇪_Германия'
            if len(cleaned) > 1: cleaned[1] += '#🇨🇭_Швейцария'
            encoded = base64.b64encode("\n".join(cleaned).encode('utf-8')).decode('utf-8')
            return web.Response(text=encoded, headers={"profile-title": f"base64:{base64.b64encode('⛩ ВОРОТА VPN ⛩'.encode('utf-8')).decode('utf-8')}", "profile-update-interval": "24"}, content_type='text/plain')
        return web.Response(text="No keys", status=404)
    except: return web.Response(text="Error", status=500)

async def admin_dashboard(request):
    if not check_auth(request): return web.Response(status=401, headers={'WWW-Authenticate': 'Basic realm="Admin Area"'}, text="Auth required")
    
    users = await db_funcs.get_all_users()
    
    srv_stats = await get_real_server_stats()
    srv_cards = ""
    for s in srv_stats:
        badge = "bg-success" if "Онлайн" in s['status'] else "bg-danger"
        srv_cards += f'<div class="col-md-6 mb-3"><div class="card bg-dark border-secondary"><div class="card-body"><h5>{s["flag"]} {s["name"]} <span class="badge {badge} float-end">{s["status"]}</span></h5><div class="d-flex justify-content-between mt-3"><div>CPU: {s["cpu"]}</div><div>RAM: {s["ram"]}</div><div>Up: {s["uptime"]}</div></div></div></div></div>'

    user_rows = ""
    for u in sorted(users, key=lambda x: x.id, reverse=True):
        sub = u.subscription_end.strftime('%d.%m.%Y') if u.subscription_end and u.subscription_end > datetime.now() else 'Нет'
        total_devs = u.device_limit + (u.extra_device_limit if u.extra_device_end and u.extra_device_end > datetime.now() else 0)
        
        user_rows += f"""
        <tr>
            <td>{u.telegram_id}</td>
            <td>@{u.username or u.full_name}</td>
            <td>{sub}</td>
            <td>{total_devs}</td>
            <td>
                <form action="/admin/action/custom_days/{u.telegram_id}" method="POST" class="d-flex gap-1 mb-1">
                    <input type="number" name="days" class="form-control form-control-sm" placeholder="± Дни" style="width: 70px;" required>
                    <button type="submit" class="btn btn-sm btn-outline-success">OK</button>
                </form>
            </td>
            <td>
                <a href="/admin/history/{u.telegram_id}" class="btn btn-sm btn-info" title="История платежей">📜 История</a>
                <a href="/admin/action/delete/{u.telegram_id}" class="btn btn-sm btn-danger" onclick="return confirm('Удалить?')">🗑</a>
            </td>
        </tr>"""

    html = f"""
    <!DOCTYPE html><html lang="ru" data-bs-theme="dark"><head><meta charset="UTF-8"><title>CRM</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body class="p-4" style="background:#0d1117;">
        <h2 class="mb-4">⛩ Админка</h2>
        <a href="/admin/action/mass_update" class="btn btn-warning mb-4" onclick="return confirm('Это обновит сервера у ВСЕХ пользователей. Продолжить?')">🔄 Обновить сервера у ВСЕХ (Добавить новые)</a>
        <div class="row">{srv_cards}</div>
        <table class="table table-dark table-bordered text-center mt-4">
            <thead><tr><th>ID</th><th>Ник</th><th>Подписка</th><th>Лимит📱</th><th>Дни</th><th>Действия</th></tr></thead>
            <tbody>{user_rows}</tbody>
        </table>
    </body></html>
    """
    return web.Response(text=html, content_type='text/html')

async def admin_history(request):
    if not check_auth(request): return web.Response(status=401)
    user_id = int(request.match_info.get('user_id'))
    payments = await db_funcs.get_user_payments(user_id)
    
    rows = "".join([f"<tr><td>{p.date.strftime('%d.%m.%Y %H:%M')}</td><td>{p.action}</td><td>{p.amount} ₽</td></tr>" for p in payments])
    html = f'<!DOCTYPE html><html data-bs-theme="dark"><head><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head><body class="p-4 bg-dark text-white"><h3>История: {user_id}</h3><a href="/admin" class="btn btn-secondary mb-3">Назад</a><table class="table table-dark"><tr><th>Дата</th><th>Действие</th><th>Сумма</th></tr>{rows}</table></body></html>'
    return web.Response(text=html, content_type='text/html')

async def admin_action(request):
    if not check_auth(request): return web.Response(status=401)
    action = request.match_info.get('action')
    user_id = request.match_info.get('user_id')
    bot = request.app['bot']
    
    if action == "mass_update":
        users = await db_funcs.get_all_users()
        for u in users:
            if u.subscription_end and u.subscription_end > datetime.now():
                total_devs = u.device_limit + (u.extra_device_limit if u.extra_device_end and u.extra_device_end > datetime.now() else 0)
                await create_vless_profile(u.telegram_id, device_limit=total_devs)
        raise web.HTTPFound('/admin')

    try:
        with Session() as session:
            user = session.query(User).filter_by(telegram_id=int(user_id)).first()
            if action == "custom_days":
                data = await request.post()
                days = int(data.get('days', 0))
                if user.subscription_end and user.subscription_end > datetime.now(): user.subscription_end += timedelta(days=days)
                else: user.subscription_end = datetime.now() + timedelta(days=days)
            elif action == "delete":
                await delete_client_by_email(str(user.telegram_id))
                session.delete(user)
            session.commit()
    except: pass
    raise web.HTTPFound('/admin')

def setup_webhook(app, bot):
    app['bot'] = bot
    app.router.add_post('/webhook', yookassa_webhook)
    app.router.add_get('/sub/{user_id}', sub_handler)
    app.router.add_get('/admin', admin_dashboard)
    app.router.add_get('/admin/history/{user_id}', admin_history)
    app.router.add_post('/admin/action/{action}/{user_id}', admin_action)
    app.router.add_get('/admin/action/{action}', admin_action) # для mass_update
    app.router.add_get('/admin/action/{action}/{user_id}', admin_action)
