import os

filename = 'src/handlers.py'
if os.path.exists(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Добавляем parse_mode='HTML' там, где бот выдает профиль
    # Ищем строку с выдачей ссылок и модифицируем её
    content = content.replace("await message.answer(text)", "await message.answer(text, parse_mode='HTML')")
    content = content.replace("await call.message.answer(text)", "await call.message.answer(text, parse_mode='HTML')")
    content = content.replace("await bot.send_message(user_id, text)", "await bot.send_message(user_id, text, parse_mode='HTML')")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Разметка HTML включена!")
else:
    print("❌ Файл handlers.py не найден")
