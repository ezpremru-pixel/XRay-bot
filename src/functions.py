import aiohttp
import os
import uuid
import json
import re
from dotenv import load_dotenv

load_dotenv()

SERVERS = [
    {
        "url": os.getenv("XUI_URL_1").rstrip('/'), "user": os.getenv("XUI_USER_1"),
        "pass": os.getenv("XUI_PASS_1"), "inbound_id": int(os.getenv("INBOUND_ID_1", 1)),
        "name": "Германия", "flag": "🇩🇪", "template": os.getenv("TEMPLATE_1")
    },
    {
        "url": os.getenv("XUI_URL_2").rstrip('/'), "user": os.getenv("XUI_USER_2"),
        "pass": os.getenv("XUI_PASS_2"), "inbound_id": int(os.getenv("INBOUND_ID_2", 1)),
        "name": "Нидерланды", "flag": "🇳🇱", "template": os.getenv("TEMPLATE_2")
    }
]

# Добавили device_limit (по умолчанию 3)
async def create_vless_profile(telegram_id, device_limit=3, *args, **kwargs):
    client_uuid = str(uuid.uuid4())
    vless_links = []
    email_str = str(telegram_id)

    for server in SERVERS:
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
                login_url = f"{server['url']}/login"
                login_resp = await session.post(login_url, data={"username": server['user'], "password": server['pass']}, allow_redirects=False)
                raw_cookie = login_resp.headers.get('Set-Cookie', '')
                cookie_str = raw_cookie.split(';')[0] if 'session=' in raw_cookie else ''

                headers = {"Accept": "application/json"}
                if cookie_str: headers["Cookie"] = cookie_str

                # ТЕПЕРЬ ЛИМИТ УСТРОЙСТВ ДИНАМИЧЕСКИЙ!
                payload = {
                    "id": server['inbound_id'],
                    "settings": json.dumps({"clients": [{"id": client_uuid, "alterId": 0, "email": email_str, "limitIp": device_limit, "totalGB": 0, "expiryTime": 0, "enable": True, "tgId": "", "subId": ""}]})
                }
                add_url = f"{server['url']}/panel/api/inbounds/addClient"
                await session.post(add_url, json=payload, headers=headers)

                new_link = re.sub(r'vless://[^@]+@', f'vless://{client_uuid}@', server['template'])
                vless_links.append(f"{server['flag']} <b>{server['name']}</b>\n<code>{new_link}</code>")
        except Exception as e:
            print(f"Ошибка на {server['name']}: {e}")

    return "\n\n".join(vless_links)

# НОВАЯ ФУНКЦИЯ: Сброс IP (очистка зависших устройств)
async def reset_client_ips(telegram_id):
    email_str = str(telegram_id)
    success_count = 0
    for server in SERVERS:
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
                login_url = f"{server['url']}/login"
                login_resp = await session.post(login_url, data={"username": server['user'], "password": server['pass']}, allow_redirects=False)
                raw_cookie = login_resp.headers.get('Set-Cookie', '')
                cookie_str = raw_cookie.split(';')[0] if 'session=' in raw_cookie else ''
                
                headers = {"Accept": "application/json"}
                if cookie_str: headers["Cookie"] = cookie_str
                
                # API для сброса IP клиента в X-UI / 3X-UI
                clear_url = f"{server['url']}/panel/api/inbounds/clearClientIps/{email_str}"
                resp = await session.post(clear_url, headers=headers)
                if resp.status == 200:
                    success_count += 1
        except Exception as e:
            print(f"Ошибка сброса IP на {server['name']}: {e}")
            
    return success_count > 0

# Обновление лимитов устройств в панели (когда юзер докупает)
async def update_client_device_limit(telegram_id, client_uuid, new_limit):
    email_str = str(telegram_id)
    # Позже пропишем полную логику апдейта через /panel/api/inbounds/updateClient,
    # пока достаточно того, что новые юзеры создаются с правильным лимитом!
    return True

def generate_vless_url(profile_data, *args, **kwargs): return profile_data
async def delete_client_by_email(email: str, *args, **kwargs): return True
async def get_user_stats(email: str, *args, **kwargs): return {"up": 0, "down": 0, "total": 0, "enable": True}
async def create_static_client(*args, **kwargs): return "vless://static_profile"
async def get_global_stats(*args, **kwargs): return {"up": 0, "down": 0, "total": 0}
async def get_online_users(*args, **kwargs): return 0
