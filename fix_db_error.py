import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем аргументы в функциях, чтобы они принимали любые данные (**kwargs)
content = content.replace("async def cmd_start(message: Message, db):", "async def cmd_start(message: Message, **kwargs):")
content = content.replace("async def show_profile(message: Message, db):", "async def show_profile(message: Message, **kwargs):")
content = content.replace("async def show_tariffs(message: Message, db):", "async def show_tariffs(message: Message, **kwargs):")
content = content.replace("async def process_tariff_selection(callback: CallbackQuery, db):", "async def process_tariff_selection(callback: CallbackQuery, **kwargs):")
content = content.replace("async def start_connect(message: Message, bot: Bot, db):", "async def start_connect(message: Message, bot: Bot, **kwargs):")

# Добавляем строчку получения db внутри каждой функции
db_line = "    db = kwargs.get('db')\n"
functions = [
    "async def cmd_start(message: Message, **kwargs):\n",
    "async def show_profile(message: Message, **kwargs):\n",
    "async def show_tariffs(message: Message, **kwargs):\n",
    "async def process_tariff_selection(callback: CallbackQuery, **kwargs):\n",
    "async def start_connect(message: Message, bot: Bot, **kwargs):\n"
]

for func in functions:
    content = content.replace(func, func + db_line)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Ошибка 'missing db' исправлена!")
