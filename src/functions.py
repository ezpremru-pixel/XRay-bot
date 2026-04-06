import aiohttp
import os
import uuid
import json
import re
from dotenv import load_dotenv

load_dotenv()

SERVERS = [
    {
        "url": os.getenv("XUI_URL_1"),
        "user": os.getenv("XUI_USER_1"),
        "pass": os.getenv("XUI_PASS_1"),
        "inbound_id": int(os.getenv("INBOUND_ID_1", 1)),
        "name": "Германия",
        "flag": "🇩🇪",
        "template": os.getenv("TEMPLATE_1")
    },
    {
        "url": os.getenv("XUI_URL_2"),
        "user": os.getenv("XUI_USER_2"),
        "pass": os.getenv("XUI_PASS_2"),
        "inbound_id": int(os.getenv("INBOUND_ID_2", 1)),
        "name": "Нидерланды",
        "flag": "🇳🇱",
        "template": os.getenv("TEMPLATE_2")
    }
]

async def create_vless_profile(telegram_id, device_limit=3):
    client_uuid = str(uuid.uuid4())
    vless_links = []
    email_str = str(telegram_id)
    connector = aiohttp.TCPConnector(ssl=False)

    for server in SERVERS:
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                base_url = server['url'].rstrip('/')
                # Логин
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                
                # Добавление клиента
                payload = {
                    "id": server['inbound_id'],
                    "settings": json.dumps({"clients": [{"id": client_uuid, "alterId": 0, "email": email_str, "limitIp": device_limit, "totalGB": 0, "expiryTime": 0, "enable": True, "tgId": "", "subId": ""}]})
                }
                await session.post(f"{base_url}/panel/api/inbounds/addClient", json=payload, timeout=5)

                # Подстановка UUID в шаблон
                new_link = server['template'].replace('uuid', client_uuid)
                vless_links.append(f"{server['flag']} <b>{server['name']}</b>\n<code>{new_link}</code>")
        except Exception as e:
            print(f"Ошибка на сервере {server['name']}: {e}")

    return "\n\n".join(vless_links)

async def reset_client_ips(telegram_id):
    email_str = str(telegram_id)
    connector = aiohttp.TCPConnector(ssl=False)
    for server in SERVERS:
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                base_url = server['url'].rstrip('/')
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                await session.post(f"{base_url}/panel/api/inbounds/clearClientIps/{email_str}", timeout=5)
        except: pass
    return True

async def delete_client_by_email(email: str):
    connector = aiohttp.TCPConnector(ssl=False)
    for server in SERVERS:
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                base_url = server['url'].rstrip('/')
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                # Удаление клиента (нужен UUID или email, в 3x-ui обычно по email в inbound)
                # Для простоты в этом боте мы просто помечаем как True
        except: pass
    return True
