import re
import os
import base64
import json
import asyncio
import logging
import traceback
import random
import aiohttp
from dotenv import load_dotenv
from aiohttp import web
from datetime import datetime, timedelta
from sqlalchemy import func

from database import Session, User, PaymentHistory, Withdrawal, Server, BotSettings
import database as db_funcs
import functions
from functions import get_real_server_stats, create_vless_profile, delete_client_by_email, reset_client_ips, get_user_traffic_and_ips

logger = logging.getLogger("WEBHOOK_API")
logger.setLevel(logging.DEBUG)

ADMIN_LOGIN, ADMIN_PASS = "admin", "vorota2026"
ADMIN_TG_ID = 8179216822
TWO_FA_SESSIONS = {}

def check_auth(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '): return False
    try:
        auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        return auth_decoded == f"{ADMIN_LOGIN}:{ADMIN_PASS}"
    except: return False

async def get_subscription(request):
    try:
        load_dotenv(override=True)
        uid_str = request.match_info.get('user_id')
        
        # ФИКС БАГА
        if not uid_str or not uid_str.isdigit():
            return web.Response(text="Invalid Request", status=400)
            
        user_id = int(uid_str)
        email_str = str(user_id)

        with Session() as db_session:
            u = db_session.query(User).filter_by(telegram_id=user_id).first()
            if u and u.is_banned:
                b64_content = base64.b64encode(b"vless://00000000-0000-0000-0000-000000000000@1.1.1.1:80?type=tcp&security=none#\xe2\x9d\x8c_\xd0\x92\xd0\xab_\xd0\x97\xd0\x90\xd0\x91\xd0\x90\xd0\x9d\xd0\x95\xd0\x9d\xd0\xab").decode('utf-8')
                return web.Response(text=b64_content, headers={"Content-Type": "application/octet-stream", "profile-title": "base64:4puEINCST1JPVEEgVPNgfA=="}, status=200)

            limit = u.device_limit if u else 3
            try: await create_vless_profile(user_id, limit)
            except: pass

        links = []
        for i, server in enumerate(functions.SERVERS):
            fresh_url = server.get('url')
            if not fresh_url: continue
            if "2.27.50.25" in fresh_url: fresh_url = fresh_url.replace("http://", "https://")
            base_url = fresh_url.rstrip('/')

            try:
                async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True), connector=aiohttp.TCPConnector(ssl=False)) as session:
                    resp = await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                    if resp.status != 200: continue
                    list_resp = await session.get(f"{base_url}/panel/api/inbounds/list", timeout=5)
                    if list_resp.status == 200:
                        data = await list_resp.json()
                        uuid_found = None
                        for inbound in data.get('obj', []):
                            if inbound.get('id') == server['inbound_id']:
                                settings = json.loads(inbound.get('settings', '{}'))
                                for client in settings.get('clients', []):
                                    if str(client.get('email')) == email_str:
                                        uuid_found = client.get('id')
                                        break
                            if uuid_found:
                                safe_name = server['name'].replace(' ', '_')
                                new_link = server['template'].replace('uuid', uuid_found)
                                base_link = new_link.split('#')[0] if '#' in new_link else new_link
                                links.append(f"{base_link}#{server['flag']}_{safe_name}")
            except: pass

        if not links: return web.Response(text="ОШИБКА ПОДПИСКИ", status=200)
        sub_content = "\n".join(links)
        b64_content = base64.b64encode(sub_content.encode('utf-8')).decode('utf-8')
        b64_name = base64.b64encode("⛩ ВОРОТА VPN ⛩".encode('utf-8')).decode('utf-8')
        return web.Response(text=b64_content, headers={"Content-Type": "application/octet-stream", "profile-title": f"base64:{b64_name}", "profile-update-interval": "24"}, status=200)
    except Exception as e:
        return web.Response(text=f"ERROR: {str(e)}", status=200)

async def admin_dashboard(request):
    if not check_auth(request): return web.Response(status=401, headers={'WWW-Authenticate': 'Basic realm="Admin"'})
    try:
        with open("src/admin.html", "r", encoding="utf-8") as f: return web.Response(text=f.read(), content_type='text/html')
    except: return web.Response(text="Файл src/admin.html не найден!", status=404)

async def request_2fa(request):
    if not check_auth(request): return web.json_response({"error": "Auth"}, status=401)
    ip = request.remote
    code = str(random.randint(100000, 999999))
    TWO_FA_SESSIONS[ip] = code
    bot = request.app.get('bot')
    if bot:
        try: await bot.send_message(ADMIN_TG_ID, f"🔐 <b>Попытка входа в Админ-Панель!</b>\nIP: {ip}\n\nКод подтверждения: <code>{code}</code>", parse_mode='HTML')
        except: pass
    return web.json_response({"status": "sent"})

async def verify_2fa(request):
    if not check_auth(request): return web.json_response({"error": "Auth"}, status=401)
    try: payload = await request.json()
    except: return web.json_response({"error": "Bad request"}, status=400)
    ip = request.remote
    if TWO_FA_SESSIONS.get(ip) == payload.get("code"):
        del TWO_FA_SESSIONS[ip]
        return web.json_response({"status": "ok"})
    return web.json_response({"status": "error", "error": "Неверный код!"})

async def api_get_data(request):
    if not check_auth(request): return web.json_response({"error": "Unauthorized"}, status=401)
    try:
        with Session() as session:
            users = session.query(User).order_by(User.id.desc()).all()
            bot_settings = session.query(BotSettings).first()
            servers_db = session.query(Server).all()
            all_withdrawals = session.query(Withdrawal).order_by(Withdrawal.date.desc()).all()
            
            u_data, p_data, w_list = [], [], []
            active_count = 0

            ref_map = {}
            for u in users:
                if u.referrer_id:
                    if u.referrer_id not in ref_map: ref_map[u.referrer_id] = []
                    ref_map[u.referrer_id].append({"id": u.telegram_id, "name": u.username or u.full_name})

            w_map = {}
            for w in all_withdrawals:
                u_link = session.query(User).filter_by(telegram_id=w.telegram_id).first()
                username = u_link.username if u_link else str(w.telegram_id)
                w_list.append({"id": w.id, "uid": w.telegram_id, "username": username, "amount": w.amount, "method": w.method, "details": w.details, "status": w.status, "date": w.date.strftime('%d.%m %H:%M')})
                if w.telegram_id not in w_map: w_map[w.telegram_id] = []
                w_map[w.telegram_id].append({"amount": w.amount, "status": w.status, "date": w.date.strftime('%d.%m %H:%M')})

            for u in users:
                is_active = u.subscription_end and u.subscription_end > datetime.now()
                if is_active: active_count += 1
                
                u_data.append({
                    "id": u.telegram_id, "username": u.username or "N/A", "full_name": u.full_name or "",
                    "sub_end": u.subscription_end.strftime('%d.%m.%Y %H:%M') if is_active else 'Истекла',
                    "limit": u.device_limit, "balance": round(u.balance, 2), "refs": u.referral_count,
                    "is_banned": u.is_banned
                })
                
                if u.referral_count > 0 or u.balance > 0 or u.earned_lvl1 > 0:
                    p_data.append({
                        "id": u.telegram_id, "username": u.username or "N/A", "balance": round(u.balance, 2),
                        "refs_lvl1": u.referral_count, "refs_lvl2": u.level2_count,
                        "earned_lvl1": round(u.earned_lvl1, 2), "earned_lvl2": round(u.earned_lvl2, 2),
                        "ref_lvl1_pct": u.custom_ref_lvl1 or 30, "ref_lvl2_pct": u.custom_ref_lvl2 or 5,
                        "invited_list": ref_map.get(u.telegram_id, []), "withdrawals": w_map.get(u.telegram_id, [])
                    })

            funnel = {
                "started": len(users),
                "tested": sum(1 for u in users if u.took_test),
                "paid": session.query(PaymentHistory).filter(PaymentHistory.amount > 0).distinct(PaymentHistory.telegram_id).count()
            }

            total_earned = session.query(func.sum(PaymentHistory.amount)).scalar() or 0
            recent_tx_db = session.query(PaymentHistory).order_by(PaymentHistory.date.desc()).limit(15).all()
            transactions = [{"date": tx.date.strftime('%d.%m %H:%M'), "amount": tx.amount, "action": tx.action, "uid": tx.telegram_id} for tx in recent_tx_db]

            settings_data = {
                "start_text": bot_settings.start_text if bot_settings else "",
                "start_image": bot_settings.start_image if bot_settings else "",
                "profile_image": bot_settings.profile_image if bot_settings else "",
                "tariffs_image": bot_settings.tariffs_image if bot_settings else "",
                "partner_image": bot_settings.partner_image if bot_settings else "",
                "proxy_link": bot_settings.proxy_link if bot_settings else ""
            }

        stats = await get_real_server_stats()
        analytics = {"total_users": len(users), "active_users": active_count, "total_earned": round(total_earned, 2), "transactions": transactions, "funnel": funnel}
        srv_data = [{"id": s.id, "name": s.name, "ip": s.ip, "flag": s.flag, "active": s.is_active} for s in servers_db]

        return web.json_response({"users": u_data, "partners": p_data, "withdrawals": w_list, "stats": stats, "servers": srv_data, "analytics": analytics, "settings": settings_data})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def run_broadcast(bot, users, text, image_url):
    success, fail = 0, 0
    for u in users:
        try:
            if image_url: await bot.send_photo(u.telegram_id, photo=image_url, caption=text, parse_mode='HTML')
            else: await bot.send_message(u.telegram_id, text, parse_mode='HTML')
            success += 1
        except: fail += 1
        await asyncio.sleep(0.05)
    logger.info(f"Рассылка завершена. Успешно: {success}, Ошибок: {fail}")

async def api_action(request):
    if not check_auth(request): return web.Response(status=401)
    act, uid = request.match_info.get('action'), request.match_info.get('user_id')
    try: payload = await request.json() if request.can_read_body else {}
    except: payload = {}

    bot = request.app.get('bot')

    try:
        with Session() as session:
            # РЕСТАРТ СЕРВЕРА 3X-UI
            if act == "restart_node":
                srv = session.query(Server).get(int(uid))
                if srv:
                    url = srv.url.replace("http://", "https://") if "2.27.50.25" in srv.url else srv.url
                    base_url = url.rstrip('/')
                    try:
                        cookie_jar = aiohttp.CookieJar(unsafe=True)
                        async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=aiohttp.TCPConnector(ssl=False)) as http_session:
                            await http_session.post(f"{base_url}/login", data={"username": srv.user, "password": srv.password}, timeout=5)
                            await http_session.post(f"{base_url}/server/restartXrayService", timeout=5) # Рестарт ядра
                            await http_session.post(f"{base_url}/panel/setting/restartPanel", timeout=5) # Рестарт панели
                    except: pass
                return web.json_response({"status": "ok", "msg": "Команда на рестарт XRay отправлена!"})

            elif act == "update_settings":
                settings = session.query(BotSettings).first()
                if settings:
                    settings.start_text = payload.get('start_text', settings.start_text)
                    settings.start_image = payload.get('start_image', settings.start_image)
                    settings.profile_image = payload.get('profile_image', settings.profile_image)
                    settings.tariffs_image = payload.get('tariffs_image', settings.tariffs_image)
                    settings.partner_image = payload.get('partner_image', settings.partner_image)
                    settings.proxy_link = payload.get('proxy_link', settings.proxy_link)
                session.commit()
                return web.json_response({"status": "ok", "msg": "Настройки обновлены"})

            elif act == "broadcast":
                msg_text = payload.get('text', '')
                img_url = payload.get('image_url', '')
                all_users = session.query(User).filter_by(is_banned=False).all()
                if bot: asyncio.create_task(run_broadcast(bot, all_users, msg_text, img_url))
                return web.json_response({"status": "ok", "msg": "Рассылка запущена"})

            elif act == "add_server":
                session.add(Server(name=payload.get('name'), url=payload.get('url'), ip=payload.get('ip'), user=payload.get('user'), password=payload.get('password'), template=payload.get('template'), flag=payload.get('flag')))
                session.commit()
                functions.SERVERS = functions.load_servers_from_db()
                return web.json_response({"status": "ok"})

            elif act == "approve_withdrawal":
                w = session.query(Withdrawal).get(int(uid))
                if w:
                    w.status = "✅ Выполнено"
                    try:
                        if bot: await bot.send_message(w.telegram_id, f"✅ <b>Ваша заявка на вывод {w.amount} ₽ успешно выполнена!</b>\nСредства отправлены на ваши реквизиты.", parse_mode='HTML')
                    except: pass
                session.commit()
                return web.json_response({"status": "ok"})

            elif act == "reject_withdrawal":
                w = session.query(Withdrawal).get(int(uid))
                reason = payload.get("reason", "Отказано администратором")
                if w:
                    w.status = "❌ Отклонено"
                    w.reject_reason = reason
                    u = session.query(User).filter_by(telegram_id=w.telegram_id).first()
                    if u: u.balance += w.amount
                    try:
                        if bot: await bot.send_message(w.telegram_id, f"❌ <b>Ваша заявка на вывод отклонена!</b>\nСредства ({w.amount} ₽) возвращены на баланс.\n\n💬 Комментарий: {reason}", parse_mode='HTML')
                    except: pass
                session.commit()
                return web.json_response({"status": "ok"})

            u = session.query(User).filter_by(telegram_id=int(uid)).first() if uid and uid.isdigit() else None
            if u:
                if act == "custom_days":
                    d = int(payload.get('days', 0))
                    u.subscription_end = (u.subscription_end if u.subscription_end and u.subscription_end > datetime.now() else datetime.now()) + timedelta(days=d)
                    if not u.is_banned: await create_vless_profile(u.telegram_id, u.device_limit)
                    u.notified_level = 0
                    try:
                        if bot: await bot.send_message(u.telegram_id, f"🎁 <b>Администратор обновил вашу подписку!</b>\nТеперь она доступна до {u.subscription_end.strftime('%d.%m.%Y')}", parse_mode='HTML')
                    except: pass
                elif act == "edit_balance":
                    amount = float(payload.get('amount', 0))
                    u.balance += amount
                    try:
                        if bot and amount > 0: await bot.send_message(u.telegram_id, f"💰 Ваш баланс изменен на <b>+{amount}₽</b> администратором.", parse_mode='HTML')
                        elif bot and amount < 0: await bot.send_message(u.telegram_id, f"💸 С вашего баланса списано <b>{abs(amount)}₽</b>.", parse_mode='HTML')
                    except: pass
                elif act == "limit_inc":
                    u.device_limit += 1
                    if not u.is_banned: await create_vless_profile(u.telegram_id, u.device_limit)
                    try:
                        if bot: await bot.send_message(u.telegram_id, f"📱 <b>Лимит устройств увеличен!</b> Теперь: {u.device_limit} шт.", parse_mode='HTML')
                    except: pass
                elif act == "limit_dec":
                    if u.device_limit > 1:
                        u.device_limit -= 1
                        if not u.is_banned: await create_vless_profile(u.telegram_id, u.device_limit)
                        try:
                            if bot: await bot.send_message(u.telegram_id, f"⚠️ <b>Лимит устройств уменьшен.</b> Теперь: {u.device_limit} шт.", parse_mode='HTML')
                        except: pass
                elif act == "toggle_ban":
                    u.is_banned = not u.is_banned
                    if u.is_banned: 
                        await delete_client_by_email(str(u.telegram_id))
                        try:
                            if bot: await bot.send_message(u.telegram_id, "❌ Ваш доступ приостановлен администратором.")
                        except: pass
                    else: 
                        await create_vless_profile(u.telegram_id, u.device_limit)
                        try:
                            if bot: await bot.send_message(u.telegram_id, "✅ Ваш доступ восстановлен!")
                        except: pass
                elif act == "set_ref_percent":
                    u.custom_ref_lvl1 = float(payload.get('lvl1', 30))
                    u.custom_ref_lvl2 = float(payload.get('lvl2', 5))
                    try:
                        if bot: await bot.send_message(u.telegram_id, f"💎 <b>Ваши реферальные проценты обновлены!</b>\n🥇 1 уровень: {u.custom_ref_lvl1}%\n🥈 2 уровень: {u.custom_ref_lvl2}%", parse_mode='HTML')
                    except: pass
                elif act == "get_user_stats":
                    stats = await get_user_traffic_and_ips(u.telegram_id)
                    return web.json_response({"status": "ok", "stats": stats})
            session.commit()
        return web.json_response({"status": "ok"})
    except Exception as e:
        logger.error(f"Ошибка в api_action ({act}): {traceback.format_exc()}")
        return web.json_response({"error": str(e)}, status=500)

async def yookassa_webhook(request):
    try:
        data = await request.json()
        if data.get('event') == 'payment.succeeded':
            obj = data['object']; meta = obj.get('metadata', {}); user_id = meta.get('user_id')
            pay_type = meta.get('type', 'sub'); tariff_key = meta.get('tariff', '1m')
            amount = float(obj['amount']['value'])

            if user_id:
                with Session() as session:
                    u = session.query(User).filter_by(telegram_id=int(user_id)).first()
                    if u:
                        now = datetime.now(); bot = request.app['bot']; ADMIN_ID = 8179216822
                        u.notified_level = 0
                        if pay_type == 'device':
                            devices_to_add = 1 if tariff_key in ['dev_test', 'dev_1'] else int(tariff_key.split('_')[1]) if '_' in tariff_key else 1
                            u.device_limit += devices_to_add
                            session.add(PaymentHistory(telegram_id=u.telegram_id, amount=amount, action=f"Покупка: +{devices_to_add} устр."))
                            await create_vless_profile(u.telegram_id, u.device_limit)
                        else:
                            days = 30
                            if tariff_key == 'test': days = 1
                            elif tariff_key == '2m': days = 60
                            elif tariff_key == '3m': days = 90
                            elif tariff_key == '6m': days = 180
                            elif tariff_key == '12m': days = 365

                            is_first = session.query(PaymentHistory).filter_by(telegram_id=u.telegram_id).count() == 0
                            bonus = 7 if (is_first and u.referrer_id) else 0
                            u.subscription_end = (u.subscription_end if u.subscription_end and u.subscription_end > now else now) + timedelta(days=days + bonus)
                            session.add(PaymentHistory(telegram_id=u.telegram_id, amount=amount, action=f"Подписка ({days} дн.)"))
                            await create_vless_profile(u.telegram_id, u.device_limit)
                        session.commit()
        return web.Response(status=200)
    except: return web.Response(status=400)

def setup_webhook(app, bot):
    app['bot'] = bot
    app.router.add_get('/admin', admin_dashboard)
    app.router.add_get('/admin/api/request_2fa', request_2fa)
    app.router.add_post('/admin/api/verify_2fa', verify_2fa)
    app.router.add_get('/admin/api/data', api_get_data)
    app.router.add_post('/admin/api/action/{user_id}/{action}', api_action)
    app.router.add_get('/sub/{user_id}', get_subscription)
    app.router.add_get('/sub/{user_id}/', get_subscription)
    app.router.add_post('/webhook', yookassa_webhook)
