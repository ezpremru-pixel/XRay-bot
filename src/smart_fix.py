import asyncio
import aiohttp
import json
from database import Session, Server

async def run():
    with Session() as db_session:
        srv = db_session.query(Server).filter_by(ip="37.46.19.132").first()
        if not srv:
            print("❌ Сервер не найден в БД!")
            return
        
        base_url = srv.url.rstrip('/')
        print(f"🔄 Пробуем зайти: {base_url}")
        
        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar(unsafe=True), connector=aiohttp.TCPConnector(ssl=False)) as session:
            resp = await session.post(f"{base_url}/login", data={"username": srv.user, "password": srv.password})
            print(f"🔑 Статус авторизации: {resp.status} (должно быть 200)")
            
            if resp.status == 200:
                list_resp = await session.get(f"{base_url}/panel/api/inbounds/list")
                data = await list_resp.json()
                
                found_id = None
                print("\n📋 Список всех Inbound в панели:")
                for inbound in data.get('obj', []):
                    inb_id = inbound.get('id')
                    print(f" - Inbound ID: {inb_id}, Remark: {inbound.get('remark')}")
                    settings = json.loads(inbound.get('settings', '{}'))
                    
                    for client in settings.get('clients', []):
                        if str(client.get('email')) == "8179216822":
                            found_id = inb_id
                            print(f"\n✅ БИНГО! Твой аккаунт найден в Inbound ID = {found_id}")
                            break
                
                if found_id:
                    srv.inbound_id = found_id
                    db_session.commit()
                    print(f"💾 База данных обновлена! Правильный Inbound ID сохранен.")
                else:
                    print("\n❌ Твой аккаунт (8179216822) вообще не найден в панели!")
            else:
                print("❌ Логин не удался. Неверный пароль или WebBasePath.")

asyncio.run(run())
