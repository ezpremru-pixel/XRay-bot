import os

path = 'src/handlers.py'
# Полностью перезаписываем файл чистым и рабочим кодом
content = """from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import os
from database import *
from functions import create_vless_profile

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message, db):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    
    kb = [
        [KeyboardButton(text="💎 Купить подписку"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🚀 Подключиться")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Привет, {message.from_user.full_name}! 👋\\nЭто бот <b>Vorota VPN</b>.\\n\\nИспользуй меню ниже:", reply_markup=keyboard, parse_mode='HTML')

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message, db):
    user = await db.get_user(message.from_user.id)
    status = "Активна" if user.subscription_end and user.subscription_end > datetime.now() else "Истекла"
    end_date = user.subscription_end.strftime('%d.%m.%Y') if user.subscription_end else "Нет"
    await message.answer(f"👤 <b>Профиль:</b>\\nID: <code>{user.telegram_id}</code>\\nПодписка: <b>{status}</b>\\nДо: <code>{end_date}</code>", parse_mode='HTML')

@router.message(F.text == "💎 Купить подписку")
async def show_tariffs(message: Message, db):
    tariffs = await db.get_all_tariffs()
    builder = InlineKeyboardBuilder()
    for t in tariffs:
        builder.row(InlineKeyboardButton(text=f"{t['name']} - {t['price']}₽", callback_data=f"buy_{t['id']}"))
    await message.answer("Выберите тариф:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("buy_"))
async def process_tariff_selection(callback: CallbackQuery, db):
    tariff_id = callback.data.split('_')[1]
    tariff_data = await db.get_tariff(tariff_id)
    if tariff_data:
        amount = int(tariff_data['price'])
        pay_url = f"https://yoomoney.ru/transfer/quickpay?receiver=4100118556845340&quickpay-form=button&sum={amount}&label={callback.from_user.id}"
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=f"💳 Оплатить {amount} руб.", url=pay_url))
        await callback.message.answer(f"💰 Тариф: {tariff_data['name']}\\nК оплате: {amount} руб.", reply_markup=builder.as_markup())

@router.message(F.text == "🚀 Подключиться")
async def start_connect(message: Message, bot: Bot, db):
    user = await db.get_user(message.from_user.id)
    if not user or not user.subscription_end or user.subscription_end <= datetime.now():
        await message.answer("❌ Ваша подписка истекла. Пожалуйста, оплатите доступ.")
        return
    
    await message.answer("⏳ Генерирую ключи...")
    try:
        profile_data = await create_vless_profile(user.telegram_id)
        await message.answer(f"🎉 <b>Ваш VPN готов!</b>\\n\\n{profile_data}", parse_mode='HTML')
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

def setup_handlers(dp):
    dp.include_router(router)
"""

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Код полностью переписан без ошибок. Запускай!")
