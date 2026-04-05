from aiohttp import web
from yookassa import Payment
import database as db_funcs
import logging

async def yookassa_webhook(request):
    # Получаем данные от ЮKassa
    data = await request.json()
    
    try:
        # Проверяем статус платежа
        event = data.get('event')
        if event == 'payment.succeeded':
            payment_obj = data.get('object')
            metadata = payment_obj.get('metadata')
            user_id = metadata.get('user_id')
            tariff_key = metadata.get('tariff')
            
            # Определяем, на сколько продлеваем (в месяцах)
            months = 1
            if tariff_key == "2m": months = 2
            elif tariff_key == "3m": months = 3
            elif tariff_key == "6m": months = 6
            elif tariff_key == "12m": months = 12
            
            # Обновляем подписку в базе
            await db_funcs.update_subscription(int(user_id), months)
            
            logging.info(f"✅ Оплата подтверждена для юзера {user_id} на {months} мес.")
            
        return web.Response(status=200)
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
        return web.Response(status=400)

def setup_webhook(app):
    app.router.add_post('/webhook', yookassa_webhook)
