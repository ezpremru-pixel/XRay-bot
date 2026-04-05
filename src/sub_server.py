import base64
import json
import sqlite3
from aiohttp import web

async def handle_sub(request):
    client_uuid = request.match_info.get('uuid')
    if not client_uuid:
        return web.Response(status=400, text="No UUID provided")
    
    # Идем в базу данных бота и ищем ключи пользователя
    try:
        conn = sqlite3.connect('../users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vless_profile_data FROM users WHERE vless_profile_data LIKE ?", ('%' + client_uuid + '%',))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            # Распаковываем JSON (у нас там будут лежать 2 ссылки)
            links = json.loads(row[0]) 
            if isinstance(links, list):
                # Склеиваем ссылки и кодируем в Base64 (стандарт для v2ray/Hiddify)
                sub_data = '\n'.join(links)
                encoded = base64.b64encode(sub_data.encode('utf-8')).decode('utf-8')
                return web.Response(text=encoded)
    except Exception as e:
        print(f"DB Error: {e}")
        
    return web.Response(status=404, text="Subscription not found")

app = web.Application()
app.add_routes([web.get('/sub/{uuid}', handle_sub)])

if __name__ == '__main__':
    print("🚀 Сервер подписок запущен на порту 8080...")
    web.run_app(app, host='0.0.0.0', port=8080)
