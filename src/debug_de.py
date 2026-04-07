import asyncio
import json
import aiohttp
from functions import SERVERS

async def test():
    server = SERVERS[0] # Германия
    print("--- ПРОВЕРКА ГЕРМАНИИ ---")
    print(f"URL из конфига: {server.get('url')}")
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True), connector=connector) as session:
        try:
            base_url = server['url'].rstrip('/')
            print("Стучимся в панель...")
            resp = await session.post(f"{base_url}/login", data={"username": server['user'], "password": server['pass']}, timeout=5)
            print(f"Статус авторизации: {resp.status} (если тут не 200 - неверный логин/пароль в .env)")
            
            list_resp = await session.get(f"{base_url}/panel/api/inbounds/list", timeout=5)
            print(f"Статус списка клиентов: {list_resp.status}")
            
            if list_resp.status == 200:
                data = await list_resp.json()
                test_email = "8179216822"
                found_user = False
                found_inbound = False
                
                for inbound in data.get('obj', []):
                    if inbound.get('id') == server['inbound_id']:
                        found_inbound = True
                        settings = json.loads(inbound.get('settings', '{}'))
                        clients = settings.get('clients', [])
                        print(f"✅ Подключение {server['inbound_id']} найдено! Всего клиентов внутри: {len(clients)}")
                        
                        for client in clients:
                            if str(client.get('email')) == test_email:
                                print(f"🎉 Юзер {test_email} НАЙДЕН в панели!")
                                found_user = True
                                break
                
                if not found_inbound:
                    print(f"❌ ОШИБКА: Подключение с ID {server['inbound_id']} вообще не существует в панели Германии!")
                elif not found_user:
                    print(f"❌ ОШИБКА: Юзер {test_email} НЕ НАЙДЕН! Боту нечего выдавать в Хап.")
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА СВЯЗИ: {type(e).__name__} - {e}")

asyncio.run(test())
