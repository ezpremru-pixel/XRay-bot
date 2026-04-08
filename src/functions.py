import aiohttp
import os
import uuid
import json
import time
import asyncio
from dotenv import load_dotenv

load_dotenv(override=True)

def load_servers_from_db():
    from database import Session, Server
    with Session() as session:
        db_servers = session.query(Server).filter_by(is_active=True).all()
        if not db_servers:
            servers_to_add = [
                {"url": os.getenv("XUI_URL_1"), "ip": "2.27.50.25", "user": os.getenv("XUI_USER_1"), "password": os.getenv("XUI_PASS_1"), "inbound_id": 1, "name": "Германия", "flag": "🇩🇪", "mon_port": 80, "template": os.getenv("TEMPLATE_1")},
                {"url": os.getenv("XUI_URL_2"), "ip": "37.46.19.132", "user": os.getenv("XUI_USER_2"), "password": os.getenv("XUI_PASS_2"), "inbound_id": 1, "name": "Нидерланды", "flag": "🇳🇱", "mon_port": 8080, "template": os.getenv("TEMPLATE_2")}
            ]
            for s in servers_to_add:
                if s["url"]:
                    session.add(Server(name=s["name"], url=s["url"], ip=s["ip"], mon_port=s["mon_port"], user=s["user"], password=s["password"], inbound_id=s["inbound_id"], template=s["template"], flag=s["flag"], is_active=True))
            session.commit()
            db_servers = session.query(Server).filter_by(is_active=True).all()
        return [{"id": s.id, "url": s.url, "ip": s.ip, "user": s.user, "pass": s.password, "inbound_id": s.inbound_id, "name": s.name, "flag": s.flag, "mon_port": s.mon_port, "template": s.template} for s in db_servers]

try: SERVERS = load_servers_from_db()
except Exception as e: SERVERS = []

# ЖЕЛЕЗОБЕТОННЫЙ TCP-ПИНГ
async def get_real_server_stats():
    stats = []
    for srv in SERVERS:
        srv_data = {"name": srv['name'], "flag": srv['flag'], "status": "🔴 Оффлайн", "cpu": "-", "ram": "-", "uptime": "-", "ping": "Ошибка"}
        try:
            start_time = time.time()
            url = srv.get('url', '')

            # Вычисляем порт панели для пинга
            port = 443 if "https://" in url else 80
            clean_url = url.replace("https://", "").replace("http://", "").split("/")[0]
            if ":" in clean_url:
                port = int(clean_url.split(":")[1])

            # Чистый TCP пинг (идеально точный)
            reader, writer = await asyncio.wait_for(asyncio.open_connection(srv['ip'], port), timeout=2.0)
            ping_ms = int((time.time() - start_time) * 1000)
            writer.close()
            await writer.wait_closed()

            srv_data["ping"] = f"{ping_ms} ms"
            srv_data["status"] = "🟢 Онлайн"

            # Если жив, пробуем забрать статистику
            try:
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                    async with session.get(f"http://{srv['ip']}:{srv['mon_port']}", timeout=2) as stat_resp:
                        if stat_resp.status == 200:
                            srv_data.update(await stat_resp.json())
            except: pass
        except Exception as e:
            pass
        stats.append(srv_data)
    return stats

async def get_user_traffic_and_ips(telegram_id):
    email_str = str(telegram_id)
    connector = aiohttp.TCPConnector(ssl=False)
    total_up, total_down = 0, 0
    active_ips = []

    for server in SERVERS:
        url = server.get('url')
        if not url: continue
        if "2.27.50.25" in url: url = url.replace("http://", "https://")
        base_url = url.rstrip('/')
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                try:
                    traff_resp = await session.get(f"{base_url}/panel/api/inbounds/getClientTraffics/{email_str}", timeout=5)
                    if traff_resp.status == 200:
                        traff_data = await traff_resp.json()
                        if traff_data.get('success') and traff_data.get('obj'):
                            obj = traff_data['obj']
                            total_up += obj.get('up', 0); total_down += obj.get('down', 0)
                except: pass
                try:
                    online_resp = await session.post(f"{base_url}/panel/api/inbounds/onlines", timeout=5)
                    if online_resp.status == 200:
                        online_data = await online_resp.json()
                        if online_data.get('success'):
                            for client in online_data.get('obj', []):
                                if client.get('email') == email_str: active_ips.append(f"{server['flag']} {client.get('ip', 'Unknown')}")
                except: pass
        except: pass

    return {"up_gb": round(total_up / (1024**3), 2), "down_gb": round(total_down / (1024**3), 2), "total_gb": round((total_up + total_down) / (1024**3), 2), "ips": active_ips}

async def create_vless_profile(telegram_id, device_limit=3):
    client_uuid, email_str, connector = str(uuid.uuid4()), str(telegram_id), aiohttp.TCPConnector(ssl=False)
    for server in SERVERS:
        url = server.get('url')
        if not url: continue
        if "2.27.50.25" in url: url = url.replace("http://", "https://")
        base_url = url.rstrip('/')
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                data = await (await session.get(f"{base_url}/panel/api/inbounds/list", timeout=5)).json()
                existing_uuid = None
                flow = ""
                
                for inbound in data.get('obj', []):
                    if inbound.get('id') == server['inbound_id']:
                        clients = json.loads(inbound.get('settings', '{}')).get('clients', [])
                        
                        # Умный поиск параметра flow (для VLESS XTLS)
                        if clients and isinstance(clients, list) and len(clients) > 0:
                            if 'flow' in clients[0] and clients[0]['flow']:
                                flow = clients[0]['flow']
                                
                        for client in clients:
                            if str(client.get('email')) == email_str:
                                existing_uuid = client.get('id'); break
                                
                client_data = {"id": existing_uuid or client_uuid, "email": email_str, "limitIp": device_limit, "totalGB": 0, "expiryTime": 0, "enable": True, "tgId": "", "subId": ""}
                
                if flow:
                    client_data["flow"] = flow
                    
                payload = {"id": server['inbound_id'], "settings": json.dumps({"clients": [client_data]})}
                
                if existing_uuid: 
                    await session.post(f"{base_url}/panel/api/inbounds/updateClient/{existing_uuid}", json=payload, timeout=5)
                else: 
                    await session.post(f"{base_url}/panel/api/inbounds/addClient", json=payload, timeout=5)
        except Exception as e:
            import logging
            logging.error(f"Failed to create profile on {server.get('name')}: {e}")
    return True

async def reset_client_ips(telegram_id):
    email_str, connector = str(telegram_id), aiohttp.TCPConnector(ssl=False)
    for server in SERVERS:
        url = server.get('url')
        if not url: continue
        if "2.27.50.25" in url: url = url.replace("http://", "https://")
        base_url = url.rstrip('/')
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                await session.post(f"{base_url}/panel/api/inbounds/clearClientIps/{email_str}", timeout=5)
        except: pass
    return True

async def delete_client_by_email(email: str):
    connector = aiohttp.TCPConnector(ssl=False)
    for server in SERVERS:
        url = server.get('url')
        if not url: continue
        if "2.27.50.25" in url: url = url.replace("http://", "https://")
        base_url = url.rstrip('/')
        try:
            cookie_jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=cookie_jar, connector=connector) as session:
                await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                await session.post(f"{base_url}/panel/api/inbounds/{server['inbound_id']}/delClient/{email}", timeout=5)
        except: pass
    return True
