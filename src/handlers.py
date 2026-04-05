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

Configuration.account_id = '1303776'
Configuration.secret_key = 'live_0WZidMCcMnMXOwhzkB4Ux1LguAfOVzGnvr0E_dvEfas'
ADMIN_ID = 8179216822

class SupportState(StatesGroup):
    waiting_for_ticket = State()
    waiting_for_answer = State()

router = Router()
TARIFFS = {
    "1m": {"name": "1 МЕСЯЦ", "price": 129, "val": 1},
    "2m": {"name": "2 МЕСЯЦА", "price": 249, "val": 2},
    "3m": {"name": "3 МЕСЯЦА", "price": 349, "val": 3},
    "6m": {"name": "6 МЕСЯЦЕВ", "price": 649, "val": 6},
    "12m": {"name": "12 МЕСЯЦЕВ", "price": 1149, "val": 12},
}

@router.message(F.text == "/start")
async def cmd_start(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if not u: await db_funcs.create_user(m.from_user.id, m.from_user.full_name, m.from_user.username)
    kb = [[KeyboardButton(text="🚀 ПОДКЛЮЧИТЬ VPN")], [KeyboardButton(text="💳 ТАРИФЫ"), KeyboardButton(text="🎁 ТЕСТ 24ч")], [KeyboardButton(text="👤 ПРОФИЛЬ"), KeyboardButton(text="🆘 ПОДДЕРЖКА")]]
    if m.from_user.id == ADMIN_ID: kb.append([KeyboardButton(text="⚙️ АДМИН ПАНЕЛЬ")])
    await m.answer("👋 <b>VOROTA VPN</b>", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode='HTML')

@router.message(F.text == "🎁 ТЕСТ 24ч")
async def gift_test(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if u.subscription_end: return await m.answer("❌ Тест уже был использован.")
    try:
        # Пытаемся выдать 1 месяц как замену 24 часам, если база не берет дни
        await db_funcs.update_subscription(u.telegram_id, 1)
        await m.answer("🎉 <b>Тест активирован!</b> (Выдано 30 дней в качестве бонуса)")
    except Exception as e:
        print(f"DB ERR: {e}")
        await m.answer("⚠️ Ошибка базы. Попробуем позже.")

@router.message(F.text == "🆘 ПОДДЕРЖКА")
async def support_start(m: Message, state: FSMContext):
    await m.answer("📝 Опишите проблему:")
    await state.set_state(SupportState.waiting_for_ticket)

@router.message(SupportState.waiting_for_ticket)
async def handle_ticket(m: Message, state: FSMContext, bot: Bot):
    await state.clear()
    b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="✍️ Ответить", callback_data=f"ans_{m.from_user.id}"))
    await bot.send_message(ADMIN_ID, f"📩 Тикет от @{m.from_user.username}:\n{m.text}", reply_markup=b.as_markup())
    await m.answer("✅ Отправлено.")

@router.callback_query(F.data.startswith("buy_"))
async def process_pay(c: CallbackQuery):
    t = TARIFFS[c.data.split("_")[1]]
    try:
        p = Payment.create({
            "amount": {"value": str(t['price']), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/hfwehdhfjvorot_bot"},
            "capture": True,
            "description": f"VPN {t['name']}",
            "metadata": {"user_id": c.from_user.id, "type": "sub"},
            "receipt": {
                "customer": {"full_name": c.from_user.full_name, "email": "customer@vorotavpn.ru"},
                "items": [{"description": f"Доступ к VPN {t['name']}", "quantity": "1.00", "amount": {"value": str(t['price']), "currency": "RUB"}, "vat_code": "1"}]
            }
        }, uuid.uuid4())
        b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="💰 ОПЛАТИТЬ", url=p.confirmation.confirmation_url))
        await c.message.answer(f"Сумма: {t['price']}₽", reply_markup=b.as_markup())
    except Exception as e:
        print(f"PAY ERROR: {e}")
        await c.message.answer("⚠️ Ошибка ЮKassa (чек).")

@router.message(F.text == "👤 ПРОФИЛЬ")
async def profile(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    d = u.subscription_end.strftime('%d.%m.%Y') if u.subscription_end else "Нет"
    await m.answer(f"👤 ID: {u.telegram_id}\nДо: {d}")

@router.message(F.text == "🚀 ПОДКЛЮЧИТЬ VPN")
async def connect(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if not u.subscription_end or u.subscription_end <= datetime.now():
        return await m.answer("⚠️ Подписка истекла.")
    await m.answer(f"<code>{await create_vless_profile(u.telegram_id)}</code>", parse_mode='HTML')

def setup_handlers(dp):
    dp.include_router(router)

@router.message(F.text == "💳 ТАРИФЫ")
async def show_tariffs_menu(m: Message):
    builder = InlineKeyboardBuilder()
    for k, t in TARIFFS.items():
        builder.row(InlineKeyboardButton(text=f"🔘 {t['name']} — {t['price']}₽", callback_data=f"buy_{k}"))
    await m.answer("💳 <b>ВЫБЕРИТЕ ТАРИФ:</b>", reply_markup=builder.as_markup(), parse_mode='HTML')

@router.message(F.text == "👤 ПРОФИЛЬ")
async def show_profile_fixed(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if u and u.subscription_end:
        d = u.subscription_end.strftime('%d.%m.%Y')
    else:
        d = "Нет"
    await m.answer(f"👤 <b>ПРОФИЛЬ</b>\n🆔 ID: <code>{m.from_user.id}</code>\n📅 Подписка до: {d}", parse_mode='HTML')
