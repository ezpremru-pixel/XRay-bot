import asyncio
import json
import aiohttp
from functions import SERVERS

async def test():
    server = SERVERS[0] # Германия
    print("--- ПРОВЕРКА ГЕРМАНИИ ---")
    print(f"URL из конфига: {server.get('url')}")
    print(f"Шаблон ссылки задан: {bool(server.get('template'))}")
    
    if not server.get('url'):
        print("❌ ОШИБКА: В файле .env не прописан XUI_URL_1")
        return
        
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True), connector=connector) as session:
        try:
            base_url = server['url'].rstrip('/')
            print(f"Стучимся в панель...")
            resp = await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
            print(f"Статус авторизации: {resp.status} (должен быть 200)")
            
            list_resp = await session.get(f"{base_url}/panel/api/inbounds/list", timeout=5)
            print(f"Статус скачивания клиентов: {list_resp.status} (должен быть 200)")
            
            if list_resp.status == 200:
                data = await list_resp.json()
                found_inbound = False
                for inbound in data.get('obj', []):
                    if inbound.get('id') == server['inbound_id']:
                        found_inbound = True
                        settings = json.loads(inbound.get('settings', '{}'))
                        clients = settings.get('clients', [])
                        print(f"✅ Инбаунд {server['inbound_id']} найден! В нём {len(clients)} клиентов.")
                if not found_inbound:
                    print(f"❌ ОШИБКА: Инбаунд с ID {server['inbound_id']} вообще не существует на сервере!")
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА СВЯЗИ: {e}")

asyncio.run(test())
