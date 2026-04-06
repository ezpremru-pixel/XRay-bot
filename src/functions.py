import aiohttp
import os
import uuid
import json
import re
from dotenv import load_dotenv

load_dotenv()

SERVERS = [
    {
        "url": "http://2.27.50.25:2053/hDFimH5nEPhSIzOJrt",
        "user": "fHc928zGl6",
        "pass": "CzCCVsc2SY",
        "inbound_id": 1,
        "name": "Германия",
        "flag": "🇩🇪",
        "template": os.getenv("TEMPLATE_1")
    },
    {
        "url": "http://37.46.19.132:2053/nwUUfGDVW3H2UoOGQM",
        "user": "fWbhg1XMvM",
        "pass": "IUh0a77YVX",
        "inbound_id": 1,
        "name": "Нидерланды",
        "flag": "🇳🇱",
        "template": os.getenv("TEMPLATE_2")
    }
]

async def get_real_server_stats():
    stats = []
    # Максимально лояльный коннектор
    connector = aiohttp.TCPConnector(ssl=False)
    for srv in SERVERS:
        srv_data = {"name": srv['name'], "flag": srv['flag'], "url": srv['url'], "status": "🔴 Оффлайн", "cpu": "0%", "ram": "0%", "uptime": "-"}
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            # Включаем unsafe=True для работы с кривыми заголовками
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                base_url = srv['url'].rstrip('/')
                
                # ЛОГИН
                async with session.post(f"{base_url}/login", 
                                        data={"username": srv['user'], "password": srv['pass']}, 
                                        timeout=10) as resp:
                    if resp.status == 200:
                        # СТАТУС
                        async with session.post(f"{base_url}/server/status", timeout=10) as st_resp:
                            if st_resp.status == 200:
                                d = await st_resp.json()
                                obj = d.get("obj", {})
                                srv_data["status"] = "🟢 Онлайн"
                                srv_data["cpu"] = f"{obj.get('cpu', 0):.1f}%"
                                srv_data["ram"] = f"{obj.get('mem', {}).get('current', 0) // 1024 // 1024} MB"
                                up = obj.get('uptime', 0)
                                srv_data["uptime"] = f"{up // 86400} дн."
        except Exception as e:
            print(f"Ошибка {srv['name']}: {e}")
        stats.append(srv_data)
    return stats

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
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=10)
                payload = {"id": server['inbound_id'], "settings": json.dumps({"clients": [{"id": client_uuid, "email": email_str, "limitIp": device_limit, "enable": True}]})}
                await session.post(f"{base_url}/panel/api/inbounds/addClient", json=payload, timeout=10)
                new_link = server['template'].replace('uuid', client_uuid)
                vless_links.append(f"{server['flag']} <b>{server['name']}</b>\n<code>{new_link}</code>")
        except: pass
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
    return True
