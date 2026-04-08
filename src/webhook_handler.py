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
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

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

async def proxy_redirect(request):
    with Session() as session:
        settings = session.query(BotSettings).first()
        proxy_url = settings.proxy_link if settings and settings.proxy_link else "https://t.me/proxy"
    raise web.HTTPFound(proxy_url)

async def get_subscription(request):
    try:
        load_dotenv(override=True)
        uid_str = request.match_info.get('user_id')

        if not uid_str or not uid_str.isdigit():
            return web.Response(text="Invalid Request", status=400)

        user_id = int(uid_str)
        email_str = str(user_id)
        domain = os.getenv('DOMAIN', 'solk.pw')
        sub_url = f"https://{domain}/sub/{user_id}"

        with Session() as db_session:
            u = db_session.query(User).filter_by(telegram_id=user_id).first()
            if u and u.is_banned:
                b64_content = base64.b64encode(b"vless://00000000-0000-0000-0000-000000000000@1.1.1.1:80?type=tcp&security=none#\xe2\x9d\x8c_\xd0\x92\xd0\xab_\xd0\x97\xd0\x90\xd0\x91\xd0\x90\xd0\x9d\xd0\x95\xd0\x9d\xd0\xab").decode('utf-8')
                return web.Response(text=b64_content, headers={"Content-Type": "application/octet-stream", "profile-title": "base64:4puEINCST1JPVEEgVPNgfA=="}, status=200)

            limit = u.device_limit if u else 3
            expiry_date = u.subscription_end.strftime('%d.%m.%Y %H:%M') if u and u.subscription_end else "Истекла"
            try: await create_vless_profile(user_id, limit)
            except: pass

        links = []
        for i, server in enumerate(functions.SERVERS):
            fresh_url = server.get('url')
            if not fresh_url: continue
            if "2.27.50.25" in fresh_url: fresh_url = fresh_url.replace("http://", "https://")
            base_url = fresh_url.rstrip('/')
            safe_name = server.get('name', f'Server_{i}').replace(' ', '_')
            server_success = False

            try:
                async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True), connector=aiohttp.TCPConnector(ssl=False)) as session:
                    pw = server.get('password', server.get('pass', ''))
                    resp = await session.post(f"{base_url}/login", data={"username": server.get('user', 'admin'), "password": pw}, timeout=5)

                    if resp.status == 200:
                        list_resp = await session.get(f"{base_url}/panel/api/inbounds/list", timeout=5)
                        if list_resp.status == 200:
                            data = await list_resp.json()
                            uuid_found = None
                            inbound_id = server.get('inbound_id', 1)

                            for inbound in data.get('obj', []):
                                if inbound.get('id') == inbound_id:
                                    settings = json.loads(inbound.get('settings', '{}'))
                                    for client in settings.get('clients', []):
                                        if str(client.get('email')) == email_str:
                                            uuid_found = client.get('id')
                                            break
                            if uuid_found:
                                template_str = server.get('template')
                                if not template_str or str(template_str).strip() in ["", "None"]:
                                    template_str = f"vless://uuid@{server.get('ip')}:{server.get('port', 443)}?type=tcp&security=none"
                                
                                new_link = template_str.replace('uuid', str(uuid_found))
                                base_link = new_link.split('#')[0] if '#' in new_link else new_link
                                flag = server.get('flag', '🏳️')
                                links.append(f"{base_link}#{flag}_{safe_name}")
                                server_success = True
            except: pass

            if not server_success: links.append(f"vless://00000000-0000-0000-0000-000000000000@1.1.1.1:80?type=tcp&security=none#❌_Сбой_{safe_name}")

        if not links: links.append("vless://00000000-0000-0000-0000-000000000000@1.1.1.1:80?type=tcp&security=none#❌_НЕТ_СЕРВЕРОВ")

        sub_content = "\n".join(links)
        b64_content = base64.b64encode(sub_content.encode('utf-8')).decode('utf-8')
        b64_name = base64.b64encode("⛩ ВОРОТА VPN ⛩".encode('utf-8')).decode('utf-8')

        user_agent = request.headers.get('User-Agent', '').lower()
        is_client = any(kw in user_agent for kw in ['v2ray', 'v2box', 'hiddify', 'streisand', 'shadowrocket', 'clash', 'surge', 'cfnetwork', 'dart', 'httpclient', 'okhttp', 'hitray', 'napsternetv'])
        is_browser = any(kw in user_agent for kw in ['mozilla', 'chrome', 'safari', 'applewebkit', 'edge', 'opera'])

        if is_client or not is_browser:
            return web.Response(text=b64_content, headers={"Content-Type": "application/octet-stream", "profile-title": f"base64:{b64_name}", "profile-update-interval": "24"}, status=200)

        vless_html = ""
        for idx, link in enumerate(links):
            safe_link = link.replace('"', '&quot;')
            server_name = link.split('#')[-1] if '#' in link else f"Сервер {idx+1}"
            vless_html += f"""
            <div class="bg-slate-800 p-4 rounded-xl mb-3 flex flex-col sm:flex-row justify-between items-start sm:items-center border border-slate-700 gap-4">
                <div class="overflow-hidden w-full">
                    <div class="font-bold text-blue-400 mb-1">{server_name}</div>
                    <div class="text-xs text-slate-500 truncate w-full">{safe_link[:60]}...</div>
                </div>
                <button onclick="navigator.clipboard.writeText('{safe_link}'); alert('Ключ скопирован!');" class="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg text-sm font-bold transition whitespace-nowrap w-full sm:w-auto text-white">Копировать</button>
            </div>
            """

        badge = '<span class="bg-gradient-to-r from-red-500 to-orange-500 text-white text-[10px] px-2 py-0.5 rounded-full font-black tracking-widest ml-2 animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.6)] whitespace-nowrap">Рекомендуем</span>'

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⛩ VOROTA VPN ⛩ | Подписка</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>⛩</text></svg>">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }}
        .glass-panel {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }}
        .os-content {{ display: none; }}
        .os-content.active {{ display: block; }}
        .os-btn.active {{ background-color: #2563eb; color: white; border-color: #2563eb; }}
    </style>
</head>
<body class="antialiased p-4 pb-20">

    <div class="max-w-3xl mx-auto pt-8">
        <div class="text-center mb-8">
            <h1 class="text-4xl font-black mb-2 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">⛩ VOROTA VPN ⛩</h1>
            <p class="text-slate-400">Управление подпиской</p>
        </div>

        <div class="grid grid-cols-2 gap-4 mb-8">
            <div class="glass-panel p-4 rounded-2xl text-center">
                <i class="fa-solid fa-hourglass-end text-xl text-purple-400 mb-2"></i>
                <div class="text-xs text-slate-400 tracking-wider font-bold mb-1">Доступна до</div>
                <div class="font-bold">{expiry_date}</div>
            </div>
            <div class="glass-panel p-4 rounded-2xl text-center">
                <i class="fa-solid fa-mobile-screen text-xl text-green-400 mb-2"></i>
                <div class="text-xs text-slate-400 tracking-wider font-bold mb-1">Лимит устройств</div>
                <div class="font-bold">{limit} шт.</div>
            </div>
        </div>

        <div class="glass-panel p-6 sm:p-8 rounded-3xl mb-8 border border-blue-500/30 relative overflow-hidden">
            <div class="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-[60px] -z-10"></div>
            <h2 class="text-xl font-bold mb-4 flex items-center gap-3"><i class="fa-solid fa-link text-blue-400"></i> Ссылка-Автонастройка</h2>
            <p class="text-slate-400 text-sm mb-4">Единая ссылка для всех приложений. Она сама загрузит и будет обновлять список серверов.</p>
            <div class="bg-slate-900 p-4 rounded-xl border border-slate-700 break-all text-sm text-blue-200 mb-4 font-mono">{sub_url}</div>
            <button onclick="navigator.clipboard.writeText('{sub_url}'); alert('Ссылка-подписка скопирована!');" class="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl transition text-lg flex justify-center items-center gap-2 shadow-lg shadow-blue-600/30">
                <i class="fa-regular fa-copy"></i> Скопировать ссылку
            </button>
        </div>

        <div class="glass-panel p-6 sm:p-8 rounded-3xl mb-10">
            <h2 class="text-xl font-bold mb-4 flex items-center gap-3"><i class="fa-solid fa-key text-yellow-400"></i> Отдельные ключи (VLESS)</h2>
            <p class="text-slate-400 text-sm mb-6">Если ваше приложение не поддерживает автонастройку по ссылке, скопируйте ключи по одному.</p>
            {vless_html}
        </div>

        <h2 class="text-2xl font-bold text-center mb-6">Быстрая настройка</h2>
        
        <div class="flex flex-wrap gap-2 justify-center mb-8">
            <button onclick="showOS('ios')" class="os-btn active px-4 py-2 rounded-xl border border-slate-600 font-bold hover:bg-slate-800 transition"><i class="fa-brands fa-apple mr-2"></i>iOS</button>
            <button onclick="showOS('android')" class="os-btn px-4 py-2 rounded-xl border border-slate-600 font-bold hover:bg-slate-800 transition"><i class="fa-brands fa-android mr-2"></i>Android</button>
            <button onclick="showOS('windows')" class="os-btn px-4 py-2 rounded-xl border border-slate-600 font-bold hover:bg-slate-800 transition"><i class="fa-brands fa-windows mr-2"></i>Windows</button>
            <button onclick="showOS('macos')" class="os-btn px-4 py-2 rounded-xl border border-slate-600 font-bold hover:bg-slate-800 transition"><i class="fa-solid fa-desktop mr-2"></i>MacOS</button>
            <button onclick="showOS('linux')" class="os-btn px-4 py-2 rounded-xl border border-slate-600 font-bold hover:bg-slate-800 transition"><i class="fa-brands fa-linux mr-2"></i>Linux</button>
            <button onclick="showOS('tv')" class="os-btn px-4 py-2 rounded-xl border border-slate-600 font-bold hover:bg-slate-800 transition"><i class="fa-solid fa-tv mr-2"></i>TV</button>
        </div>

        <div id="os-ios" class="os-content active">
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-blue-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 1. Установка приложения</h3>
                <p class="text-sm text-slate-300 mb-4">Откройте страницу в App Store и установите приложение. Запустите его, в окне разрешения VPN-конфигурации нажмите Allow и введите свой пароль.</p>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <a href="https://apps.apple.com/us/app/hiddify-proxy-vpn/id6596777532" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold flex items-center justify-center"><i class="fa-brands fa-apple mr-2"></i>Hiddify {badge}</a>
                    <a href="https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-brands fa-apple mr-2"></i>V2Box</a>
                    <a href="https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-brands fa-apple mr-2"></i>Hit Proxy</a>
                    <a href="https://apps.apple.com/us/app/happ-proxy-utility/id6504287215" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-brands fa-apple mr-2"></i>Happ</a>
                    <a href="https://apps.apple.com/us/app/npv-tunnel/id1629465476" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-brands fa-apple mr-2"></i>NPV Tunnel</a>
                    <a href="https://apps.apple.com/us/app/streisand/id6450534064" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-brands fa-apple mr-2"></i>Streisand</a>
                </div>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-purple-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 2. Добавление подписки</h3>
                <p class="text-sm text-slate-300 mb-4">Нажмите кнопку ниже (в зависимости от вашей программы) — приложение откроется, и подписка добавится автоматически.</p>
                <div class="flex flex-col gap-3">
                    <a href="hiddify://install-config?url={sub_url}&name=VOROTA_VPN" class="block w-full text-center bg-indigo-600 py-3 rounded-xl font-bold hover:bg-indigo-500 transition shadow-lg shadow-indigo-500/30">➕ Добавить в Hiddify</a>
                    <a href="v2box://install-sub?url={sub_url}&name=VOROTA_VPN" class="block w-full text-center bg-purple-600 py-3 rounded-xl font-bold hover:bg-purple-500 transition shadow-lg shadow-purple-500/30">➕ Добавить в V2Box</a>
                    <a href="happ://add/{sub_url}" class="block w-full text-center bg-green-600 py-3 rounded-xl font-bold hover:bg-green-500 transition shadow-lg shadow-green-500/30">➕ Добавить в Happ</a>
                    
                    <a href="#" onclick="navigator.clipboard.writeText('{sub_url}'); alert('Ссылка скопирована! Откройте приложение Hit Proxy и вставьте её.'); return false;" class="block w-full text-center bg-blue-600 py-3 rounded-xl font-bold hover:bg-blue-500 transition shadow-lg shadow-blue-500/30">➕ Добавить в Hit Proxy</a>
                    <a href="#" onclick="navigator.clipboard.writeText('{sub_url}'); alert('Ссылка скопирована! Откройте приложение NPV Tunnel и вставьте её.'); return false;" class="block w-full text-center bg-teal-600 py-3 rounded-xl font-bold hover:bg-teal-500 transition shadow-lg shadow-teal-500/30">➕ Добавить в NPV Tunnel</a>
                    <a href="#" onclick="navigator.clipboard.writeText('{sub_url}'); alert('Ссылка скопирована! Откройте приложение Streisand и вставьте её.'); return false;" class="block w-full text-center bg-orange-600 py-3 rounded-xl font-bold hover:bg-orange-500 transition shadow-lg shadow-orange-500/30">➕ Добавить в Streisand</a>
                </div>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-green-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 3. Подключение и использование</h3>
                <p class="text-sm text-slate-300">В главном разделе нажмите большую кнопку включения в центре для подключения к VPN. Не забудьте выбрать сервер в списке серверов (вкладка Configs). При необходимости выберите другой.</p>
            </div>
        </div>

        <div id="os-android" class="os-content">
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-blue-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 1. Установка приложения</h3>
                <p class="text-sm text-slate-300 mb-4">Установите приложение из Google Play. Разрешите создание VPN-соединения при первом запуске.</p>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <a href="https://play.google.com/store/apps/details?id=app.hiddify.com" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold flex items-center justify-center"><i class="fa-brands fa-google-play mr-2"></i>Hiddify {badge}</a>
                    <a href="https://play.google.com/store/apps/details?id=com.happproxy" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-brands fa-google-play mr-2"></i>Happ</a>
                    <a href="https://play.google.com/store/apps/details?id=com.v2raytun.android" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-brands fa-google-play mr-2"></i>v2rayTun</a>
                    <a href="https://play.google.com/store/apps/details?id=io.hitray.android" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-brands fa-google-play mr-2"></i>HitRay</a>
                    <a href="https://play.google.com/store/apps/details?id=com.napsternetlabs.napsternetv&hl=en" target="_blank" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold sm:col-span-2"><i class="fa-brands fa-google-play mr-2"></i>NapsternetV</a>
                </div>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-purple-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 2. Добавление подписки</h3>
                <p class="text-sm text-slate-300 mb-4">Выберите ваше приложение для автоматического импорта (если кнопка не сработала — скопируйте Ссылку-Автонастройку сверху):</p>
                <div class="flex flex-col gap-3">
                    <a href="hiddify://install-config?url={sub_url}&name=VOROTA_VPN" class="block w-full text-center bg-indigo-600 py-3 rounded-xl font-bold hover:bg-indigo-500 transition shadow-lg shadow-indigo-500/30">➕ Добавить в Hiddify</a>
                    <a href="happ://add/{sub_url}" class="block w-full text-center bg-green-600 py-3 rounded-xl font-bold hover:bg-green-500 transition shadow-lg shadow-green-500/30">➕ Добавить в Happ</a>
                    <a href="v2raytun://install-sub?url={sub_url}" class="block w-full text-center bg-blue-600 py-3 rounded-xl font-bold hover:bg-blue-500 transition shadow-lg shadow-blue-500/30">➕ Добавить в v2rayTun</a>
                    <a href="hitray://add/{sub_url}" class="block w-full text-center bg-orange-600 py-3 rounded-xl font-bold hover:bg-orange-500 transition shadow-lg shadow-orange-500/30">➕ Добавить в HitRay</a>
                    <a href="napsternetv://add/{sub_url}" class="block w-full text-center bg-teal-600 py-3 rounded-xl font-bold hover:bg-teal-500 transition shadow-lg shadow-teal-500/30">➕ Добавить в NapsternetV</a>
                </div>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-green-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 3. Подключение и использование</h3>
                <p class="text-sm text-slate-300">Нажмите большую кнопку в центре для подключения к VPN. Если интернет медленный, разверните список серверов и выберите другой.</p>
            </div>
        </div>

        <div id="os-windows" class="os-content">
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-blue-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 1. Установка программы</h3>
                <p class="text-sm text-slate-300 mb-4">Скачайте установщик и установите программу на ПК.</p>
                <div class="flex flex-col gap-3">
                    <a href="https://github.com/hiddify/hiddify-app/releases/download/v4.1.1/Hiddify-Windows-Setup-x64.exe" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold flex items-center justify-center"><i class="fa-solid fa-download mr-2"></i>Hiddify (.exe) {badge}</a>
                    <a href="https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-solid fa-download mr-2"></i>Happ (.exe)</a>
                    <a href="https://github.com/mdf45/v2raytun/releases/download/v3.8.11/v2RayTun_Setup.exe" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold"><i class="fa-solid fa-download mr-2"></i>v2rayTun (.exe)</a>
                </div>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-purple-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 2. Добавление подписки</h3>
                <p class="text-sm text-slate-300 mb-4">Нажмите кнопку ниже, разрешите браузер открыть приложение, и сервера загрузятся сами.</p>
                <div class="flex flex-col gap-3">
                    <a href="hiddify://install-config?url={sub_url}&name=VOROTA_VPN" class="block w-full text-center bg-indigo-600 py-3 rounded-xl font-bold hover:bg-indigo-500 transition shadow-lg shadow-indigo-500/30">➕ Добавить в Hiddify</a>
                    <a href="happ://add/{sub_url}" class="block w-full text-center bg-green-600 py-3 rounded-xl font-bold hover:bg-green-500 transition shadow-lg shadow-green-500/30">➕ Добавить в Happ</a>
                    <a href="v2raytun://install-sub?url={sub_url}" class="block w-full text-center bg-blue-600 py-3 rounded-xl font-bold hover:bg-blue-500 transition shadow-lg shadow-blue-500/30">➕ Добавить в v2rayTun</a>
                </div>
                <p class="text-xs text-slate-500 text-center mt-3">Важно: На Windows автодобавление может не сработать. Если не вышло — просто скопируйте Ссылку-Автонастройку и вставьте в программу вручную.</p>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-green-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 3. Подключение</h3>
                <p class="text-sm text-slate-300">Нажмите большую круглую кнопку включения. Сбоку можно выбрать конкретный сервер.</p>
            </div>
        </div>

        <div id="os-macos" class="os-content">
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-blue-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 1. Установка программы</h3>
                <p class="text-sm text-slate-300 mb-4">Скачайте образ программы и перетяните в папку Программы (Applications).</p>
                <div class="flex flex-col sm:flex-row gap-3">
                    <a href="https://github.com/hiddify/hiddify-app/releases/download/v4.1.1/Hiddify-MacOS.dmg" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold flex-1 flex items-center justify-center"><i class="fa-solid fa-download mr-2"></i>Hiddify (.dmg) {badge}</a>
                    <a href="https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.macOS.universal.dmg" class="bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold flex-1"><i class="fa-solid fa-download mr-2"></i>Happ (.dmg)</a>
                </div>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-purple-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 2. Добавление подписки</h3>
                <div class="flex flex-col gap-3">
                    <a href="hiddify://install-config?url={sub_url}&name=VOROTA_VPN" class="block w-full text-center bg-indigo-600 py-3 rounded-xl font-bold hover:bg-indigo-500 transition shadow-lg shadow-indigo-500/30">➕ Добавить в Hiddify</a>
                    <a href="happ://add/{sub_url}" class="block w-full text-center bg-green-600 py-3 rounded-xl font-bold hover:bg-green-500 transition shadow-lg shadow-green-500/30">➕ Добавить в Happ</a>
                </div>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-green-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 3. Подключение</h3>
                <p class="text-sm text-slate-300">Нажмите кнопку включения в приложении. Сервера можно менять в списке конфигураций.</p>
            </div>
        </div>

        <div id="os-linux" class="os-content">
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-blue-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 1. Установка</h3>
                <p class="text-sm text-slate-300 mb-4">Скачайте AppImage, дайте права на выполнение (chmod +x) и запустите.</p>
                <a href="https://github.com/hiddify/hiddify-next/releases/latest/download/Hiddify-Linux-x64.AppImage" class="block bg-slate-800 py-3 px-4 rounded-lg hover:bg-slate-700 border border-slate-600 text-sm text-center font-bold w-full mb-3 flex items-center justify-center"><i class="fa-brands fa-linux mr-2"></i>Hiddify (.AppImage) {badge}</a>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-purple-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 2. Настройка</h3>
                <p class="text-sm text-slate-300 mb-4">Скопируйте Ссылку-Автонастройку (в самом верху страницы) и вставьте её в разделе подписок программы. Нажмите обновить.</p>
            </div>
        </div>

        <div id="os-tv" class="os-content">
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-blue-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 1. Установка</h3>
                <p class="text-sm text-slate-300 mb-4">На телевизоре откройте Google Play Store и найдите приложение <b>Hiddify</b> или <b>v2rayTun</b>. Либо скачайте их APK вручную через приложение Downloader.</p>
            </div>
            <div class="glass-panel p-6 rounded-3xl mb-4 border-l-4 border-l-purple-500">
                <h3 class="font-bold text-lg mb-2 text-white">Шаг 2. Настройка</h3>
                <p class="text-sm text-slate-300 mb-4">В меню приложения выберите "Новая подписка" (или Группы), вставьте <b>Ссылку-Автонастройку</b> с этой страницы. Затем нажмите кнопку "Обновить".</p>
            </div>
        </div>

    </div>

    <script>
        function showOS(osName) {{
            document.querySelectorAll('.os-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.os-btn').forEach(el => {{
                el.classList.remove('active', 'bg-blue-600', 'text-white');
            }});
            
            document.getElementById('os-' + osName).classList.add('active');
            
            const activeBtn = Array.from(document.querySelectorAll('.os-btn')).find(btn => btn.getAttribute('onclick').includes(osName));
            if(activeBtn) {{
                activeBtn.classList.add('active', 'bg-blue-600', 'text-white');
            }}
        }}
    </script>
</body>
</html>"""
        return web.Response(text=html, content_type='text/html', status=200)

    except Exception as e:
        logger.error(f"Глобальная ошибка подписки: {e}")
        err_b64 = base64.b64encode(b"vless://00000000-0000-0000-0000-000000000000@1.1.1.1:80?type=tcp&security=none#\xe2\x9d\x8c_ERROR").decode('utf-8')
        return web.Response(text=err_b64, headers={"Content-Type": "application/octet-stream"}, status=200)

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
                    "is_banned": u.is_banned,
                    "has_payment_method": bool(u.payment_method_id),
                    "card_last4": u.card_last4
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

async def run_broadcast(bot, users, text, image_url, btn_text=None, btn_url=None):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    b = None
    if btn_text and btn_url:
        b = InlineKeyboardBuilder().row(InlineKeyboardButton(text=btn_text, url=btn_url)).as_markup()
        
    success, fail = 0, 0
    for u in users:
        try:
            if image_url: await bot.send_photo(u.telegram_id, photo=image_url, caption=text, parse_mode='HTML', reply_markup=b)
            else: await bot.send_message(u.telegram_id, text, parse_mode='HTML', reply_markup=b)
            success += 1
        except: fail += 1
        await asyncio.sleep(0.05)

async def api_action(request):
    if not check_auth(request): return web.Response(status=401)
    act, uid = request.match_info.get('action'), request.match_info.get('user_id')
    try: payload = await request.json() if request.can_read_body else {}
    except: payload = {}

    bot = request.app.get('bot')

    try:
        with Session() as session:
            if act == "restart_node":
                srv = session.query(Server).get(int(uid))
                if srv:
                    url = srv.url.replace("http://", "https://") if "2.27.50.25" in srv.url else srv.url
                    base_url = url.rstrip('/')
                    try:
                        cookie_jar = aiohttp.CookieJar(unsafe=True)
                        async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=aiohttp.TCPConnector(ssl=False)) as http_session:
                            await http_session.post(f"{base_url}/login", data={"username": srv.user, "password": srv.password}, timeout=5)
                            await http_session.post(f"{base_url}/server/restartXrayService", timeout=5)
                            await http_session.post(f"{base_url}/panel/setting/restartPanel", timeout=5)
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
                btn_text = payload.get('button_text')
                btn_url = payload.get('button_url')
                
                all_users = session.query(User).filter_by(is_banned=False).all()
                if bot: asyncio.create_task(run_broadcast(bot, all_users, msg_text, img_url, btn_text, btn_url))
                return web.json_response({"status": "ok", "msg": "Рассылка запущена"})

            elif act == "add_server":
                session.add(Server(name=payload.get('name'), url=payload.get('url'), ip=payload.get('ip'), user=payload.get('user'), password=payload.get('password'), template=payload.get('template'), flag=payload.get('flag')))
                session.commit()
                functions.SERVERS = functions.load_servers_from_db()
                return web.json_response({"status": "ok"})

            elif act == "delete_server":
                srv = session.query(Server).get(int(uid))
                if srv:
                    session.delete(srv)
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
        body = await request.text()
        logger.info(f"🔔 ВЕБХУК ОТ ЮKASSA: {body}")
        data = json.loads(body)
        
        # --- ЛОВИМ ОТКАЗ ОТ АВТОПЛАТЕЖА ---
        if data.get('event') == 'payment.canceled':
            obj = data['object']
            user_id = obj.get('metadata', {}).get('user_id')
            if user_id:
                with Session() as session:
                    u = session.query(User).filter_by(telegram_id=int(user_id)).first()
                    if u and u.payment_method_id:
                        u.payment_method_id = None
                        u.card_last4 = None
                        session.commit()
                        try:
                            bot = request.app['bot']
                            await bot.send_message(u.telegram_id, "❌ Ваш банк отклонил разрешение на автоплатеж (СБП/Карта). Привязка удалена.", parse_mode='HTML')
                        except: pass
            return web.Response(status=200)

        # --- ЛОВИМ УСПЕШНУЮ ОПЛАТУ ---
        if data.get('event') == 'payment.succeeded':
            obj = data['object']
            meta = obj.get('metadata', {})
            user_id = meta.get('user_id')
            pay_type = meta.get('type', 'sub')
            tariff_key = meta.get('tariff', '1m')
            amount = float(obj['amount']['value'])

            payment_method_id = None
            card_last4 = None
            
            if obj.get('payment_method') and obj.get('payment_method').get('saved'):
                payment_method_id = obj['payment_method']['id']
                pm_type = obj['payment_method'].get('type')
                
                if pm_type == 'bank_card' and obj['payment_method'].get('card'):
                    card_last4 = "*" + str(obj['payment_method']['card'].get('last4'))
                elif pm_type == 'sbp':
                    card_last4 = "СБП"
                elif pm_type == 'sberbank':
                    card_last4 = "SberPay"
                elif pm_type == 'yoo_money':
                    card_last4 = "ЮMoney"
                else:
                    card_last4 = "Автоплатеж"

            if user_id:
                with Session() as session:
                    u = session.query(User).filter_by(telegram_id=int(user_id)).first()
                    if u:
                        now = datetime.now()
                        bot = request.app['bot']
                        ADMIN_ID = 8179216822
                        u.notified_level = 0

                        if payment_method_id:
                            u.payment_method_id = payment_method_id
                            u.card_last4 = card_last4

                        if pay_type == 'device':
                            devices_to_add = 1 if tariff_key in ['dev_test', 'dev_1'] else int(tariff_key.split('_')[1]) if '_' in tariff_key else 1
                            u.device_limit += devices_to_add
                            session.add(PaymentHistory(telegram_id=u.telegram_id, amount=amount, action=f"Покупка: +{devices_to_add} устр."))
                            await create_vless_profile(u.telegram_id, u.device_limit)
                            
                            try: await bot.send_message(u.telegram_id, f"✅ <b>Оплата {amount} ₽ успешно получена!</b>\nЛимит устройств расширен. Теперь у вас: <b>{u.device_limit} шт.</b>", parse_mode='HTML')
                            except: pass
                        else:
                            days = 30
                            if tariff_key == 'test': days = 1
                            elif tariff_key == 'test1m': days = 30
                            elif tariff_key == '2m': days = 60
                            elif tariff_key == '3m': days = 90
                            elif tariff_key == '6m': days = 180
                            elif tariff_key == '12m': days = 365

                            is_first = session.query(PaymentHistory).filter_by(telegram_id=u.telegram_id).count() == 0
                            bonus = 7 if (is_first and u.referrer_id) else 0
                            
                            u.subscription_end = (u.subscription_end if u.subscription_end and u.subscription_end > now else now) + timedelta(days=days + bonus)
                            
                            act_str = f"Подписка ТЕСТ ({days} дн.)" if "test" in tariff_key else f"Подписка ({days} дн.)"
                            session.add(PaymentHistory(telegram_id=u.telegram_id, amount=amount, action=act_str))
                            
                            await create_vless_profile(u.telegram_id, u.device_limit)
                            
                            try: await bot.send_message(u.telegram_id, f"✅ <b>Оплата {amount} ₽ успешно получена!</b>\nВаша подписка продлена до <b>{u.subscription_end.strftime('%d.%m.%Y %H:%M')}</b>.", parse_mode='HTML')
                            except: pass
                            
                        session.commit()
                        
                        try:
                            method_name = card_last4 if card_last4 else "Разовая оплата (Без привязки)"
                            await bot.send_message(ADMIN_ID, f"💰 <b>УСПЕШНАЯ ОПЛАТА!</b>\n\n👤 Пользователь: <code>{u.telegram_id}</code>\n💵 Сумма: <b>{amount} ₽</b>\n💳 Способ: <b>{method_name}</b>\n\n✅ Подписка активна до: {u.subscription_end.strftime('%d.%m.%Y %H:%M')}", parse_mode='HTML')
                        except: pass
                        
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Ошибка вебхука: {e}")
        return web.Response(status=400)

def setup_webhook(app, bot):
    app['bot'] = bot
    app.router.add_get('/admin', admin_dashboard)
    app.router.add_get('/admin/', admin_dashboard)
    app.router.add_get('/sub/proxy', proxy_redirect)
    app.router.add_get('/sub/proxy/', proxy_redirect)
    app.router.add_get('/admin/api/request_2fa', request_2fa)
    app.router.add_post('/admin/api/verify_2fa', verify_2fa)
    app.router.add_get('/admin/api/data', api_get_data)
    app.router.add_post('/admin/api/action/{user_id}/{action}', api_action)
    app.router.add_get('/adminapi/request_2fa', request_2fa)
    app.router.add_post('/adminapi/verify_2fa', verify_2fa)
    app.router.add_get('/adminapi/data', api_get_data)
    app.router.add_post('/adminapi/action/{user_id}/{action}', api_action)
    app.router.add_post('/webhook', yookassa_webhook)
    app.router.add_post('/webhook/', yookassa_webhook)
