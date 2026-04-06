from aiohttp import web
import database as db_funcs
import logging
import base64

async def yookassa_webhook(request):
    data = await request.json()
    try:
        event = data.get('event')
        if event == 'payment.succeeded':
            payment_obj = data.get('object')
            metadata = payment_obj.get('metadata')
            
            user_id = metadata.get('user_id')
            tariff_key = metadata.get('tariff')
            amount = payment_obj.get('amount', {}).get('value')
            
            logging.info(f"💰 ПЛАТЕЖ ПРИШЕЛ! | Юзер ID: {user_id} | Тариф: {tariff_key} | Сумма: {amount} руб.")
            
            months = 1
            if tariff_key == "2m": months = 2
            elif tariff_key == "3m": months = 3
            elif tariff_key == "6m": months = 6
            elif tariff_key == "12m": months = 12
            elif tariff_key == "test": months = 1 # За 1 рубль даем 1 месяц для теста
            
            await db_funcs.update_subscription(int(user_id), months)
            logging.info(f"✅ Юзеру {user_id} успешно выдана подписка на {months} мес.")
            
        return web.Response(status=200)
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
        return web.Response(status=400)

# Это генератор твоей единой ссылки
async def sub_handler(request):
    user_id = request.match_info.get('user_id')
    try:
        user = await db_funcs.get_user(int(user_id))
        # Проверяем, есть ли юзер и активна ли подписка
        if not user or not user.subscription_end or user.subscription_end < __import__('datetime').datetime.now():
            return web.Response(text="Subscription expired or not found", status=403)

        # Пока берем то, что есть в базе. 
        # Позже мы изменим эту логику, чтобы бот собирал ключи с 2-х хостов.
        keys = user.vless_profile_data 
        if keys:
            # Приложения XRay понимают подписки только в формате Base64
            encoded_keys = base64.b64encode(keys.encode('utf-8')).decode('utf-8')
            return web.Response(text=encoded_keys, content_type='text/plain')
        else:
            return web.Response(text="No keys generated yet", status=404)
    except Exception as e:
        return web.Response(text="Internal Server Error", status=500)

def setup_webhook(app):
    app.router.add_post('/webhook', yookassa_webhook)
    # Добавили маршрут для короткой ссылки
    app.router.add_get('/sub/{user_id}', sub_handler)
