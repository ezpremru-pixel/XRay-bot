import os
import uuid
import json
import time
import asyncio
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(override=True)

def load_servers_from_db():
    from database import Session, Server
    with Session() as session:
        db_servers = session.query(Server).filter_by(is_active=True).all()
        if not db_servers:
            return []
        return [{"id": s.id, "url": s.url, "ip": s.ip, "user": s.user, "pass": s.password, "inbound_id": s.inbound_id, "name": s.name, "flag": s.flag, "mon_port": s.mon_port, "template": s.template} for s in db_servers]

try: 
    SERVERS = load_servers_from_db()
except: 
    SERVERS = []

async def get_real_server_stats():
    stats = []
    for srv in SERVERS:
        srv_data = {"name": srv['name'], "flag": srv['flag'], "status": "🔴 Оффлайн", "cpu": "-", "ram": "-", "uptime": "-", "ping": "Ошибка"}
        try:
            start_time = time.time()
            port = 443 if "https://" in srv['url'] else 80
            clean_url = srv['url'].replace("https://", "").replace("http://", "").split("/")[0]
            if ":" in clean_url: port = int(clean_url.split(":")[1])
            reader, writer = await asyncio.wait_for(asyncio.open_connection(srv['ip'], port), timeout=1.5)
            ping_ms = int((time.time() - start_time) * 1000)
            writer.close()
            await writer.wait_closed()
            srv_data["ping"], srv_data["status"] = f"{ping_ms} ms", "🟢 Онлайн"
            try:
                r = requests.get(f"http://{srv['ip']}:{srv['mon_port']}", timeout=2)
                if r.status_code == 200: srv_data.update(r.json())
            except: pass
        except: pass
        stats.append(srv_data)
    return stats

async def get_user_traffic_and_ips(telegram_id):
    total_up, total_down, active_ips = 0, 0, []
    for server in SERVERS:
        email = str(telegram_id) # ТЕПЕРЬ БЕЗ ПРЕФИКСОВ
        base_url = server['url'].rstrip('/')
        try:
            with requests.Session() as s:
                s.verify = False
                s.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                t_r = s.get(f"{base_url}/panel/api/inbounds/getClientTraffics/{email}", timeout=5).json()
                if t_r.get('success') and t_r.get('obj'):
                    total_up += t_r['obj'].get('up', 0); total_down += t_r['obj'].get('down', 0)
                o_r = s.post(f"{base_url}/panel/api/inbounds/onlines", timeout=5).json()
                if o_r.get('success'):
                    for c in o_r.get('obj', []):
                        if c.get('email') == email: active_ips.append(f"{server['flag']} {c.get('ip', 'Unknown')}")
        except: pass
    return {"up_gb": round(total_up/(1024**3), 2), "down_gb": round(total_down/(1024**3), 2), "total_gb": round((total_up+total_down)/(1024**3), 2), "ips": active_ips}

async def create_vless_profile(telegram_id, device_limit=3):
    client_uuid = str(uuid.uuid4())
    for server in SERVERS:
        email = str(telegram_id) # ТЕПЕРЬ БЕЗ ПРЕФИКСОВ
        base_url = server['url'].rstrip('/')
        try:
            with requests.Session() as s:
                s.verify = False
                s.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=10)
                inbounds = s.get(f"{base_url}/panel/api/inbounds/list", timeout=10).json()
                existing_uuid, flow = None, ""
                for ib in inbounds.get('obj', []):
                    if ib.get('id') == server['inbound_id']:
                        sets = json.loads(ib.get('settings', '{}'))
                        clients = sets.get('clients', [])
                        if clients and 'flow' in clients[0]: flow = clients[0]['flow']
                        for c in clients:
                            if str(c.get('email')) == email:
                                existing_uuid = c.get('id'); break
                c_data = {"id": existing_uuid or client_uuid, "email": email, "limitIp": device_limit, "totalGB": 0, "expiryTime": 0, "enable": True, "tgId": str(telegram_id), "subId": str(telegram_id)}
                if flow: c_data["flow"] = flow
                payload = {"id": server['inbound_id'], "settings": json.dumps({"clients": [c_data]})}
                if existing_uuid:
                    s.post(f"{base_url}/panel/api/inbounds/updateClient/{existing_uuid}", json=payload, timeout=10)
                else:
                    s.post(f"{base_url}/panel/api/inbounds/addClient", json=payload, timeout=10)
        except Exception as e:
            import logging
            logging.error(f"Error on {server['name']}: {e}")
    return client_uuid

async def reset_client_ips(telegram_id):
    for server in SERVERS:
        email = str(telegram_id)
        try:
            with requests.Session() as s:
                s.verify = False
                s.post(f"{server['url'].rstrip('/')}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                s.post(f"{server['url'].rstrip('/')}/panel/api/inbounds/clearClientIps/{email}", timeout=5)
        except: pass
    return True

async def delete_client_by_email(telegram_id: str):
    for server in SERVERS:
        email = str(telegram_id)
        try:
            with requests.Session() as s:
                s.verify = False
                s.post(f"{server['url'].rstrip('/')}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
                s.post(f"{server['url'].rstrip('/')}/panel/api/inbounds/{server['inbound_id']}/delClient/{email}", timeout=5)
        except: pass
    return True
