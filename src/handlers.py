from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import uuid
from yookassa import Configuration, Payment
import database as db_funcs
from functions import create_vless_profile

# Данные ЮKassa
Configuration.account_id = '1303776'
Configuration.secret_key = 'live_0WZidMCcMnMXOwhzkB4Ux1LguAfOVzGnvr0E_dvEfas'
ADMIN_ID = 8179216822 

class SupportState(StatesGroup):
    waiting_for_ticket = State()
    waiting_for_answer = State()

router = Router()

TARIFFS = {
    "1m": {"name": "💎 1 МЕСЯЦ", "price": 129},
    "2m": {"name": "💎 2 МЕСЯЦА", "price": 249},
    "3m": {"name": "💎 3 МЕСЯЦА", "price": 349},
    "6m": {"name": "💎 6 МЕСЯЦЕВ", "price": 649},
    "12m": {"name": "💎 12 МЕСЯЦЕВ", "price": 1149},
}

@router.message(F.text == "/start")
async def cmd_start(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if not u: await db_funcs.create_user(m.from_user.id, m.from_user.full_name, m.from_user.username)
    
    kb = [
        [KeyboardButton(text="🚀 ПОДКЛЮЧИТЬ VPN")],
        [KeyboardButton(text="💳 ТАРИФЫ"), KeyboardButton(text="🎁 ТЕСТ 24ч")],
        [KeyboardButton(text="👤 ПРОФИЛЬ"), KeyboardButton(text="📖 ИНСТРУКЦИЯ")],
        [KeyboardButton(text="🆘 ПОДДЕРЖКА")]
    ]
    if m.from_user.id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ АДМИН ПАНЕЛЬ")])

    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await m.answer("✨ <b>VOROTA VPN</b>\nТвой личный ключ к свободному интернету.", reply_markup=keyboard, parse_mode='HTML')

# --- ИНСТРУКЦИИ ---
@router.message(F.text == "📖 ИНСТРУКЦИЯ")
async def show_help(m: Message):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🍏 iOS", callback_data="help_ios"), InlineKeyboardButton(text="🤖 Android", callback_data="help_android"))
    b.row(InlineKeyboardButton(text="💻 PC (Windows/Mac)", callback_data="help_pc"))
    await m.answer("👇 <b>Выберите ваше устройство:</b>", reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data.startswith("help_"))
async def process_help(c: CallbackQuery):
    device = c.data.split("_")[1]
    if device == "ios":
        text = "🍏 <b>Для iPhone:</b>\n1. Скачай <b>V2Box</b>.\n2. Нажми '🚀 ПОДКЛЮЧИТЬ' и скопируй ключ.\n3. В приложении нажми '+' -> 'Import from Clipboard'."
    elif device == "android":
        text = "🤖 <b>Для Android:</b>\n1. Скачай <b>v2rayNG</b>.\n2. Скопируй ключ из бота.\n3. Нажми '+' -> 'Import from Clipboard'."
    else:
        text = "💻 <b>Для ПК:</b>\n1. Скачай <b>v2rayN</b>.\n2. Скопируй ключ.\n3. Вставь через 'Servers' -> 'Add VLESS server'."
    await c.message.answer(text, parse_mode='HTML')

# --- ТЕСТ 24 ЧАСА ---
@router.message(F.text == "🎁 ТЕСТ 24ч")
async def gift_test(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if u and u.subscription_end:
        return await m.answer("❌ Вы уже использовали тест.")
    try:
        await db_funcs.update_subscription(u.telegram_id, 1)
        await m.answer("🎉 <b>Тест активирован!</b> (Выдано 30 дней бонусом)")
    except:
        await m.answer("⚠️ Ошибка активации.")

# --- ТАРИФЫ И ОПЛАТА ---
@router.message(F.text == "💳 ТАРИФЫ")
async def show_tariffs(m: Message):
    builder = InlineKeyboardBuilder()
    for k, t in TARIFFS.items():
        builder.row(InlineKeyboardButton(text=f"🔘 {t['name']} — {t['price']}₽", callback_data=f"buy_{k}"))
    await m.answer("💳 <b>ВЫБЕРИТЕ ТАРИФ:</b>", reply_markup=builder.as_markup(), parse_mode='HTML')

@router.callback_query(F.data.startswith("buy_"))
async def process_pay(c: CallbackQuery):
    t = TARIFFS[c.data.split("_")[1]]
    try:
        p = Payment.create({
            "amount": {"value": str(t['price']), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/hfwehdhfjvorot_bot"},
            "capture": True,
            "description": f"VPN {t['name']}",
            "metadata": {"user_id": c.from_user.id, "tariff": c.data.split("_")[1]},
            "receipt": {
                "customer": {"full_name": c.from_user.full_name, "email": "customer@vorotavpn.ru"},
                "items": [{
                    "description": f"VPN {t['name']}",
                    "quantity": "1.00",
                    "amount": {"value": str(t['price']), "currency": "RUB"},
                    "vat_code": "1",
                    "payment_subject": "service",
                    "payment_mode": "full_payment"
                }]
            }
        }, uuid.uuid4())
        b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="💰 ОПЛАТИТЬ", url=p.confirmation.confirmation_url))
        await c.message.answer(f"🛒 Тариф: {t['name']}\nСумма: {t['price']}₽", reply_markup=b.as_markup())
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка ЮKassa: {e}")

# --- ПРОФИЛЬ И ПОДКЛЮЧЕНИЕ ---
@router.message(F.text == "👤 ПРОФИЛЬ")
async def profile(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    d = u.subscription_end.strftime('%d.%m.%Y') if u.subscription_end else "Нет"
    await m.answer(f"👤 <b>ПРОФИЛЬ</b>\n🆔 ID: <code>{m.from_user.id}</code>\n📅 Подписка до: {d}", parse_mode='HTML')

@router.message(F.text == "🚀 ПОДКЛЮЧИТЬ VPN")
async def connect(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if not u.subscription_end or u.subscription_end <= datetime.now():
        return await m.answer("⚠️ Подписка истекла.")
    await m.answer("📡 Генерирую ключ...")
    res = await create_vless_profile(u.telegram_id)
    await m.answer(f"<code>{res}</code>", parse_mode='HTML')

# --- ПОДДЕРЖКА ---
@router.message(F.text == "🆘 ПОДДЕРЖКА")
async def support_start(m: Message, state: FSMContext):
    await m.answer("📝 Опишите проблему:")
    await state.set_state(SupportState.waiting_for_ticket)

@router.message(SupportState.waiting_for_ticket)
async def handle_ticket(m: Message, state: FSMContext, bot: Bot):
    await state.clear()
    b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="✍️ Ответить", callback_data=f"ans_{m.from_user.id}"))
    await bot.send_message(ADMIN_ID, f"📩 Тикет от @{m.from_user.username}:\n{m.text}", reply_markup=b.as_markup())
    await message.answer("✅ Отправлено поддержке.")

@router.callback_query(F.data.startswith("ans_"))
async def start_answer(c: CallbackQuery, state: FSMContext):
    await state.update_data(answer_to=c.data.split("_")[1])
    await c.message.answer("Пиши ответ:")
    await state.set_state(SupportState.waiting_for_answer)

@router.message(SupportState.waiting_for_answer)
async def send_answer(m: Message, state: FSMContext, bot: Bot):
    uid = (await state.get_data()).get("answer_to")
    await state.clear()
    await bot.send_message(uid, f"👨‍💻 Ответ поддержки: {m.text}")
    await m.answer("✅ Отправлено.")

def setup_handlers(dp):
    dp.include_router(router)
