import os

def patch_file(path):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем создание бота, добавляя дефолтный парс-мод
    if "DefaultBotProperties" not in content:
        content = content.replace(
            "from aiogram import Bot, Dispatcher", 
            "from aiogram import Bot, Dispatcher\nfrom aiogram.client.default import DefaultBotProperties"
        )
        content = content.replace(
            "Bot(token=config.bot_token.get_secret_value())",
            "Bot(token=config.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode='HTML'))"
        )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

patch_file('src/app.py')
print("✅ Глобальный HTML-режим активирован в app.py!")
