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

# --- РЕАЛЬНЫЙ МОНИТОРИНГ ---
async def get_real_server_stats():
    stats = []
    connector = aiohttp.TCPConnector(ssl=False) # Игнорим ошибки сертификата
    for srv in SERVERS:
        srv_data = {"name": srv['name'], "flag": srv['flag'], "url": srv['url'], "status": "🔴 Оффлайн", "cpu": "0%", "ram": "0%", "uptime": "-"}
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
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
        except: pass
        stats.append(srv_data)
    return stats

# --- ВЕБХУК ОПЛАТЫ ---
async def yookassa_webhook(request):
    data = await request.json()
    bot = request.app['bot']
    try:
        if data.get('event') == 'payment.succeeded':
            p_obj = data.get('object')
            user_id = int(p_obj.get('metadata').get('user_id'))
            t_key = p_obj.get('metadata').get('tariff')
            amount = float(p_obj.get('amount', {}).get('value', 0))
            is_dev = p_obj.get('metadata').get('type') == 'device'
            
            with Session() as session:
                u = session.query(User).filter_by(telegram_id=user_id).first()
                if u:
                    desc = f"Оплата VPN ({t_key})" if not is_dev else "Доп. устройство"
                    session.add(PaymentHistory(telegram_id=user_id, amount=amount, action=desc))
                    now = datetime.now()
                    if is_dev:
                        u.extra_device_limit += 1
                        u.extra_device_end = now + timedelta(days=30)
                    else:
                        days = 30
                        if t_key == "2m": days = 60
                        elif t_key == "3m": days = 90
                        if u.subscription_end and u.subscription_end > now: u.subscription_end += timedelta(days=days)
                        else: u.subscription_end = now + timedelta(days=days)
                    session.commit()
            await bot.send_message(user_id, "✅ Оплата принята! Спасибо.")
        return web.Response(status=200)
    except: return web.Response(status=400)

# --- САБ-ЛИНК ---
async def sub_handler(request):
    user_id = request.match_info.get('user_id')
    u = await db_funcs.get_user(int(user_id))
    if not u or not u.subscription_end or u.subscription_end < datetime.now(): return web.Response(status=403)
    if u.vless_profile_data:
        vless_raw = re.findall(r'(vless://[^\s<>"\']+)', u.vless_profile_data)
        cleaned = [l.split('#')[0] for l in vless_raw]
        if len(cleaned) > 0: cleaned[0] += '#🇩🇪_Германия'
        if len(cleaned) > 1: cleaned[1] += '#🇨🇭_Швейцария'
        encoded = base64.b64encode("\n".join(cleaned).encode('utf-8')).decode('utf-8')
        return web.Response(text=encoded, headers={"profile-title": f"base64:{base64.b64encode('⛩ ВОРОТА VPN ⛩'.encode('utf-8')).decode('utf-8')}"})
    return web.Response(status=404)

# --- АДМИНКА С ТАБАМИ ---
async def admin_dashboard(request):
    if not check_auth(request): return web.Response(status=401, headers={'WWW-Authenticate': 'Basic realm="Admin Area"'})
    users = await db_funcs.get_all_users()
    srv_stats = await get_real_server_stats()
    
    srv_html = "".join([f'<div class="col-md-6 mb-3"><div class="card bg-dark border-secondary"><div class="card-body"><h5>{s["flag"]} {s["name"]} <span class="badge {"bg-success" if "Онлайн" in s["status"] else "bg-danger"} float-end">{s["status"]}</span></h5><div class="d-flex justify-content-between mt-2"><span>CPU: {s["cpu"]}</span><span>RAM: {s["ram"]}</span><span>Up: {s["uptime"]}</span></div></div></div></div>' for s in srv_stats])
    
    user_rows = ""
    ref_rows = ""
    for u in sorted(users, key=lambda x: x.id, reverse=True):
        sub = u.subscription_end.strftime('%d.%m.%Y') if u.subscription_end and u.subscription_end > datetime.now() else 'Нет'
        total_devs = u.device_limit + (u.extra_device_limit if u.extra_device_end and u.extra_device_end > datetime.now() else 0)
        
        user_rows += f'<tr><td>{u.telegram_id}</td><td>@{u.username}</td><td>{sub}</td><td>{total_devs}</td><td><form action="/admin/action/custom_days/{u.telegram_id}" method="POST" class="d-flex gap-1"><input type="number" name="days" class="form-control form-control-sm" style="width:60px" required><button class="btn btn-sm btn-success">OK</button></form></td><td><a href="/admin/history/{u.telegram_id}" class="btn btn-sm btn-info">📜</a> <a href="/admin/action/add_dev/{u.telegram_id}" class="btn btn-sm btn-warning">📱+1</a> <a href="/admin/action/delete/{u.telegram_id}" class="btn btn-sm btn-danger">🗑</a></td></tr>'
        if u.referral_count > 0 or u.balance > 0:
            ref_rows += f'<tr><td>{u.telegram_id}</td><td>@{u.username}</td><td>{u.referral_count}</td><td>{u.balance:.2f} ₽</td><td>{u.referrer_id or "-"}</td></tr>'

    html = f"""
    <!DOCTYPE html><html lang="ru" data-bs-theme="dark"><head><meta charset="UTF-8"><title>CRM</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"><script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script></head>
    <body class="p-4" style="background:#0d1117;">
        <h2 class="mb-4 text-primary">⛩ Админ-панель VOROTA</h2>
        <ul class="nav nav-tabs mb-4">
            <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#t1">👥 Юзеры</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#t2">🤝 Рефералы</button></li>
            <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#t3">🖥 Мониторинг</button></li>
        </ul>
        <div class="tab-content">
            <div class="tab-pane fade show active" id="t1"><table class="table table-dark table-striped text-center"><thead><tr><th>ID</th><th>Ник</th><th>Подписка</th><th>Лимит</th><th>± Дни</th><th>Действия</th></tr></thead><tbody>{user_rows}</tbody></table></div>
            <div class="tab-pane fade" id="t2"><table class="table table-dark table-striped text-center"><thead><tr><th>ID</th><th>Ник</th><th>Рефы</th><th>Баланс</th><th>Кто позвал</th></tr></thead><tbody>{ref_rows}</tbody></table></div>
            <div class="tab-pane fade" id="t3"><div class="row">{srv_html}</div><div class="mt-4"><a href="/admin/action/mass_update" class="btn btn-outline-warning">🔄 Массово обновить ключи (Добавить страны всем)</a></div></div>
        </div>
    </body></html>
    """
    return web.Response(text=html, content_type='text/html')

async def admin_history(request):
    if not check_auth(request): return web.Response(status=401)
    uid = int(request.match_info.get('user_id'))
    p = await db_funcs.get_user_payments(uid)
    rows = "".join([f"<tr><td>{x.date.strftime('%d.%m.%Y')}</td><td>{x.action}</td><td>{x.amount} ₽</td></tr>" for x in p])
    return web.Response(text=f'<!DOCTYPE html><html data-bs-theme="dark"><head><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head><body class="p-4 bg-dark text-white"><h3>История {uid}</h3><table class="table table-dark"><tr><th>Дата</th><th>Что сделано</th><th>Сумма</th></tr>{rows}</table><br><a href="/admin" class="btn btn-secondary">Назад</a></body></html>', content_type='text/html')

async def admin_action(request):
    if not check_auth(request): return web.Response(status=401)
    act = request.match_info.get('action')
    uid = request.match_info.get('user_id')
    bot = request.app['bot']
    
    try:
        with Session() as session:
            if act == "mass_update":
                users = await db_funcs.get_all_users(with_subscription=True)
                for u in users: await create_vless_profile(u.telegram_id, device_limit=u.device_limit)
            else:
                u = session.query(User).filter_by(telegram_id=int(uid)).first()
                if act == "custom_days":
                    d = int((await request.post()).get('days', 0))
                    if u.subscription_end and u.subscription_end > datetime.now(): u.subscription_end += timedelta(days=d)
                    else: u.subscription_end = datetime.now() + timedelta(days=d)
                    await bot.send_message(u.telegram_id, f"📅 Админ изменил вашу подписку на {d} дн.")
                elif act == "add_dev":
                    u.device_limit += 1
                    await bot.send_message(u.telegram_id, f"📱 Лимит устройств увеличен до {u.device_limit}")
                    await create_vless_profile(u.telegram_id, device_limit=u.device_limit)
                elif act == "delete":
                    await delete_client_by_email(str(u.telegram_id))
                    session.delete(u)
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
    app.router.add_get('/admin/action/{action}/{user_id}', admin_action)
    app.router.add_get('/admin/action/{action}', admin_action)
