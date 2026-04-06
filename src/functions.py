import aiohttp
import os
import uuid
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Собираем список серверов из .env
SERVERS = [
    {
        "url": os.getenv("XUI_URL_1").rstrip('/'),
        "user": os.getenv("XUI_USER_1"),
        "pass": os.getenv("XUI_PASS_1"),
        "inbound_id": int(os.getenv("INBOUND_ID_1", 1)),
        "name": "Германия",
        "flag": "🇩🇪",
        "template": os.getenv("TEMPLATE_1")
    },
    {
        "url": os.getenv("XUI_URL_2").rstrip('/'),
        "user": os.getenv("XUI_USER_2"),
        "pass": os.getenv("XUI_PASS_2"),
        "inbound_id": int(os.getenv("INBOUND_ID_2", 1)),
        "name": "Нидерланды",
        "flag": "🇳🇱",
        "template": os.getenv("TEMPLATE_2")
    }
]

async def get_real_server_stats():
    stats = []
    # Используем базовый коннектор без лишних проверок
    connector = aiohttp.TCPConnector(ssl=False)
    for srv in SERVERS:
        srv_data = {"name": srv['name'], "flag": srv['flag'], "url": srv['url'], "status": "🔴 Оффлайн", "cpu": "0%", "ram": "0%", "uptime": "-"}
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                base_url = srv['url']
                # В 3X-UI логин идет по адресу: база/login
                login_url = f"{base_url}/login"
                
                async with session.post(login_url, data={"username": srv['user'], "password": srv['pass']}, timeout=5) as resp:
                    if resp.status == 200:
                        # Если залогинились, запрашиваем статус
                        status_url = f"{base_url}/server/status"
                        async with session.post(status_url, timeout=5) as status_resp:
                            if status_resp.status == 200:
                                data = await status_resp.json()
                                obj = data.get("obj", {})
                                srv_data["status"] = "🟢 Онлайн"
                                srv_data["cpu"] = f"{obj.get('cpu', 0):.1f}%"
                                srv_data["ram"] = f"{obj.get('mem', {}).get('current', 0) // 1024 // 1024} MB"
                                uptime_seconds = obj.get('uptime', 0)
                                srv_data["uptime"] = f"{uptime_seconds // 86400} дн."
        except Exception as e:
            print(f"Ошибка мониторинга {srv['name']}: {e}")
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
                base_url = server['url']
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=10)
                
                payload = {
                    "id": server['inbound_id'],
                    "settings": json.dumps({
                        "clients": [{
                            "id": client_uuid, 
                            "alterId": 0, 
                            "email": email_str, 
                            "limitIp": device_limit, 
                            "totalGB": 0, 
                            "expiryTime": 0, 
                            "enable": True, 
                            "tgId": "", 
                            "subId": ""
                        }]
                    })
                }
                await session.post(f"{base_url}/panel/api/inbounds/addClient", json=payload, timeout=10)

                new_link = server['template'].replace('uuid', client_uuid)
                vless_links.append(f"{server['flag']} <b>{server['name']}</b>\n<code>{new_link}</code>")
        except Exception as e:
            print(f"Ошибка создания на сервере {server['name']}: {e}")

    return "\n\n".join(vless_links)

async def reset_client_ips(telegram_id):
    email_str = str(telegram_id)
    connector = aiohttp.TCPConnector(ssl=False)
    for server in SERVERS:
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                await session.post(f"{server['url']}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                await session.post(f"{server['url']}/panel/api/inbounds/clearClientIps/{email_str}", timeout=5)
        except: pass
    return True

async def delete_client_by_email(email: str):
    return True
