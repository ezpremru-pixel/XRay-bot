import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем импорт ReplyKeyboardMarkup для кнопок меню
if "from aiogram.types import" in content:
    content = content.replace("from aiogram.types import", "from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,")

# Добавляем саму функцию /start в начало роутера
start_cmd = """
@router.message(F.text == "/start")
async def cmd_start(message: Message, db):
    # Регистрируем пользователя, если его нет
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    
    # Создаем кнопки главного меню
    kb = [
        [KeyboardButton(text="💎 Купить подписку"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🚀 Подключиться"), KeyboardButton(text="Help")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        f"Привет, {message.from_user.full_name}! 👋\nЭто бот <b>Vorota VPN</b>.\n\n"
        "Нажми '💎 Купить подписку', чтобы получить доступ.",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message, db):
    user = await db.get_user(message.from_user.id)
    status = "Активна" if user.subscription_end and user.subscription_end > datetime.now() else "Истекла"
    end_date = user.subscription_end.strftime('%d.%m.%Y') if user.subscription_end else "Нет"
    
    await message.answer(
        f"👤 <b>Ваш профиль:</b>\n"
        f"ID: <code>{user.telegram_id}</code>\n"
        f"Подписка: <b>{status}</b>\n"
        f"Действует до: <code>{end_date}</code>",
        parse_mode='HTML'
    )

@router.message(F.text == "💎 Купить подписку")
async def show_tariffs(message: Message, db):
    tariffs = await db.get_all_tariffs()
    builder = InlineKeyboardBuilder()
    for t in tariffs:
        builder.row(InlineKeyboardButton(text=f"{t['name']} - {t['price']}₽", callback_data=f"buy_{t['id']}"))
    
    await message.answer("Выберите подходящий тариф:", reply_markup=builder.as_markup())

@router.message(F.text == "🚀 Подключиться")
async def start_connect(message: Message, bot: Bot, db):
    # Эмулируем нажатие инлайн-кнопки для функции connect_profile
    class FakeCall:
        def __init__(self, message, user):
            self.message = message
            self.from_user = user
            self.data = "connect_profile"
        async def answer(self, text=None, show_alert=False): pass
    
    await connect_profile(FakeCall(message, message.from_user), bot, db)
"""

# Вставляем новые функции после объявления роутера
content = content.replace("router = Router()", "router = Router()\n" + start_cmd)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Команды меню и /start возвращены!")
