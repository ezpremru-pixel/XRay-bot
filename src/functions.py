import aiohttp
import os
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Твои данные серверов
SERVERS = [
    {
        "url": "http://2.27.50.25:2053/hDFimH5nEPhSIzOJrt",
        "ip": "2.27.50.25",
        "user": "fHc928zGl6",
        "pass": "CzCCVsc2SY",
        "inbound_id": 1,
        "name": "Германия",
        "flag": "🇩🇪",
        "mon_port": 80, # Теперь стучимся на 80 порт
        "template": os.getenv("TEMPLATE_1")
    },
    {
        "url": "http://37.46.19.132:2053/nwUUfGDVW3H2UoOGQM",
        "ip": "37.46.19.132",
        "user": "fWbhg1XMvM",
        "pass": "IUh0a77YVX",
        "inbound_id": 1,
        "name": "Нидерланды",
        "flag": "🇳🇱",
        "mon_port": 80, # И тут на 80 порт
        "template": os.getenv("TEMPLATE_2")
    }
]

# --- МОНИТОРИНГ ЧЕРЕЗ АГЕНТА (ПОРТ 80) ---
async def get_real_server_stats():
    stats = []
    async with aiohttp.ClientSession() as session:
        for srv in SERVERS:
            srv_data = {"name": srv['name'], "flag": srv['flag'], "status": "🔴 Оффлайн", "cpu": "0%", "ram": "0%", "uptime": "-"}
            try:
                # Стучимся к нашему Агенту на 80 порт
                async with session.get(f"http://{srv['ip']}:{srv['mon_port']}", timeout=3) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        srv_data.update(data)
            except Exception as e:
                print(f"Ошибка мониторинга {srv['name']}: {e}")
            stats.append(srv_data)
    return stats

# --- УПРАВЛЕНИЕ КЛЮЧАМИ (X-UI API ПОРТ 2053) ---
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
                
                payload = {
                    "id": server['inbound_id'],
                    "settings": json.dumps({
                        "clients": [{
                            "id": client_uuid, "alterId": 0, "email": email_str, 
                            "limitIp": device_limit, "totalGB": 0, "expiryTime": 0, 
                            "enable": True, "tgId": "", "subId": ""
                        }]
                    })
                }
                await session.post(f"{base_url}/panel/api/inbounds/addClient", json=payload, timeout=10)
                new_link = server['template'].replace('uuid', client_uuid)
                vless_links.append(f"{server['flag']} <b>{server['name']}</b>\n<code>{new_link}</code>")
        except Exception as e:
            print(f"Ошибка создания {server['name']}: {e}")
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
