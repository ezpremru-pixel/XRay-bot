import asyncio
import json
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv(override=True)
URL = os.getenv('XUI_URL_1')
USER = os.getenv('XUI_USER_1')
PASS = os.getenv('XUI_PASS_1')
INBOUND = 1
EMAIL = "8179216822"

async def run():
    print(f"--- ДИАГНОСТИКА ГЕРМАНИИ ---")
    print(f"URL из конфига: {URL}")
    if not URL:
        print("❌ URL пустой!")
        return
        
    async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True), connector=aiohttp.TCPConnector(ssl=False)) as session:
        try:
            base = URL.rstrip('/')
            print("1. Логин в панель...")
            res = await session.post(f"{base}/login", data={"username":USER, "password":PASS}, timeout=5)
            print(f"Статус логина: {res.status}")
            if res.status != 200:
                print("❌ ОШИБКА АВТОРИЗАЦИИ (проверь логин/пароль в .env)")
                return
            
            print("2. Скачивание списка клиентов...")
            res2 = await session.get(f"{base}/panel/api/inbounds/list", timeout=5)
            print(f"Статус списка: {res2.status}")
            data = await res2.json()
            
            found_user = False
            for obj in data.get('obj', []):
                if obj.get('id') == INBOUND:
                    settings = json.loads(obj.get('settings', '{}'))
                    clients = settings.get('clients', [])
                    print(f"✅ Подключение {INBOUND} найдено! Клиентов внутри: {len(clients)}")
                    for c in clients:
                        if str(c.get('email')) == EMAIL:
                            print(f"🎉 УСПЕХ: Твой ID {EMAIL} найден! UUID: {c.get('id')}")
                            found_user = True
            
            if not found_user:
                print(f"❌ ОШИБКА: Твоего ID {EMAIL} нет в панели Германии!")
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {type(e).__name__} - {e}")

asyncio.run(run())
