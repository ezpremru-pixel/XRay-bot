import os
import re

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Добавляем проверку подписки перед выдачей ключей
check_logic = """
    user = await db.get_user(callback.from_user.id)
    if not user or not user.subscription_end or user.subscription_end <= datetime.now():
        await callback.answer("❌ Ваша подписка истекла. Пожалуйста, оплатите доступ.", show_alert=True)
        return
"""
# Вставляем проверку в начало функции connect_profile
content = re.sub(r'async def connect_profile\(callback: CallbackQuery.*?\):', 
                 f'async def connect_profile(callback: CallbackQuery, bot: Bot, db: Database):\n{check_logic}', 
                 content, flags=re.DOTALL)

# 2. Меняем стандартный платеж на прямую ссылку (простой вариант для ЮMoney)
# Мы заменим вызов send_invoice на обычное сообщение с кнопкой-ссылкой
pay_fix = """
    # Формируем ссылку на перевод (пример для ЮMoney)
    amount = int(tariff_data['price'])
    pay_url = f"https://yoomoney.ru/transfer/quickpay?receiver=4100118556845340&quickpay-form=button&sum={amount}&label={callback.from_user.id}"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Оплатить в браузере", url=pay_url))
    await callback.message.answer(f"💰 К оплате {amount} руб. за тариф '{tariff_data['name']}'", reply_markup=builder.as_markup())
"""
# Это замена блока, где бот шлет инвойс
content = re.sub(r'await bot\.send_invoice\(.*?\)', pay_fix, content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Проверка подписки добавлена, платежи переведены на внешние ссылки!")
