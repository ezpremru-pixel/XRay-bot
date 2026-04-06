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
    "test": {"name": "🧪 ТЕСТ ОПЛАТЫ", "price": 1},
    "1m": {"name": "💎 1 МЕСЯЦ", "price": 129},
    "2m": {"name": "💎 2 МЕСЯЦА", "price": 249},
    "3m": {"name": "💎 3 МЕСЯЦА", "price": 349},
    "6m": {"name": "💎 6 МЕСЯЦЕВ", "price": 649},
    "12m": {"name": "💎 12 МЕСЯЦЕВ", "price": 1149},
}

DEVICE_TARIFFS = {
    "dev_1": {"name": "+1 Устройство", "price": 29},
    "dev_2": {"name": "+2 Устройства", "price": 58},
    "dev_3": {"name": "+3 Устройства", "price": 87},
    "dev_4": {"name": "+4 Устройства", "price": 116},
    "dev_5": {"name": "+5 Устройств", "price": 145},
}

@router.message(F.text == "/start")
async def cmd_start(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if not u: await db_funcs.create_user(m.from_user.id, m.from_user.full_name, m.from_user.username)
    
    # НОВОЕ МЕНЮ
    kb = [
        [KeyboardButton(text="🚀 ПОДКЛЮЧИТЬ VPN")],
        [KeyboardButton(text="💳 ТАРИФЫ"), KeyboardButton(text="🎁 ТЕСТ 24ч")],
        [KeyboardButton(text="👤 ПРОФИЛЬ"), KeyboardButton(text="🌐 БЕСПЛАТНЫЙ ПРОКСИ")],
        [KeyboardButton(text="🆘 ПОДДЕРЖКА")]
    ]
    if m.from_user.id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ АДМИН ПАНЕЛЬ")])

    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await m.answer("✨ <b>VOROTA VPN</b>\nТвой личный ключ к свободному интернету.", reply_markup=keyboard, parse_mode='HTML')

# --- БЕСПЛАТНЫЙ ПРОКСИ ---
@router.message(F.text == "🌐 БЕСПЛАТНЫЙ ПРОКСИ")
async def free_proxy(m: Message):
    # Заглушка, сюда вставим реальную ссылку на твой MTProto/Socks5
    text = (
        "🌐 <b>БЕСПЛАТНЫЙ ПРОКСИ ДЛЯ TELEGRAM</b>\n\n"
        "Нажмите на ссылку ниже, чтобы Telegram работал без зависаний:\n\n"
        "👉 <a href='https://t.me/socks?server=127.0.0.1&port=1080&user=user&pass=pass'>ПОДКЛЮЧИТЬ ПРОКСИ</a>\n\n"
        "<i>*Прокси работает только для приложения Telegram. Для всего телефона нужен VPN.</i>"
    )
    await m.answer(text, disable_web_page_preview=True, parse_mode='HTML')

# --- ТЕСТ 24 ЧАСА (ФИКС) ---
@router.message(F.text == "🎁 ТЕСТ 24ч")
async def gift_test(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    # Надежная проверка: если юзер уже сгенерировал ключи, значит он брал тест или подписку
    if u and u.vless_profile_data:
        return await m.answer("❌ Вы уже использовали тестовый период или имеете подписку.")
    try:
        await db_funcs.update_subscription(u.telegram_id, 1) # Выдаем 1 месяц
        await m.answer("🎉 <b>Тест активирован!</b> (Выдано 30 дней бонусом)\n\nЖми «🚀 ПОДКЛЮЧИТЬ VPN».")
    except:
        await m.answer("⚠️ Ошибка активации базы.")

# --- ТАРИФЫ (VPN) ---
@router.message(F.text == "💳 ТАРИФЫ")
async def show_tariffs(m: Message):
    builder = InlineKeyboardBuilder()
    for k, t in TARIFFS.items():
        builder.row(InlineKeyboardButton(text=f"🔘 {t['name']} — {t['price']}₽", callback_data=f"buy_{k}"))
    await m.answer("💳 <b>ВЫБЕРИТЕ ТАРИФ VPN:</b>", reply_markup=builder.as_markup(), parse_mode='HTML')

# --- ПРОФИЛЬ, УСТРОЙСТВА И ИНСТРУКЦИЯ ---
@router.message(F.text == "👤 ПРОФИЛЬ")
async def profile(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    d = u.subscription_end.strftime('%d.%m.%Y') if u.subscription_end else "Нет"
    
    # Логика устройств (пока визуальная заглушка на 3, реальную цифру будем брать из базы позже)
    devices_total = 3 
    devices_used = 1 # Тут будет функция проверки онлайна
    
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📖 ИНСТРУКЦИЯ", callback_data="show_instructions"))
    b.row(InlineKeyboardButton(text="📱 Докупить устройства", callback_data="buy_devices"))
    b.row(InlineKeyboardButton(text="🗑 Управление устройствами", callback_data="manage_devices"))
    
    text = (
        f"👤 <b>ВАШ ПРОФИЛЬ</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{m.from_user.id}</code>\n"
        f"📅 Подписка до: <b>{d}</b>\n\n"
        f"📱 <b>Устройства (Лимит IPs): {devices_used}/{devices_total}</b>\n"
        f"<i>По умолчанию доступно 3 устройства. Если вам нужно подключить больше гаджетов, вы можете расширить лимит.</i>"
    )
    await m.answer(text, reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data == "show_instructions")
async def show_help_inline(c: CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🍏 iOS", callback_data="help_ios"), InlineKeyboardButton(text="🤖 Android", callback_data="help_android"))
    b.row(InlineKeyboardButton(text="💻 PC (Windows/Mac)", callback_data="help_pc"))
    await c.message.answer("👇 <b>Выберите ваше устройство:</b>", reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data.startswith("help_"))
async def process_help(c: CallbackQuery):
    device = c.data.split("_")[1]
    if device == "ios":
        text = "🍏 <b>Для iPhone:</b>\n1. Скачай <b>V2Box</b>.\n2. Скопируй свою ссылку (Подключить VPN).\n3. В приложении: Configs -> '+' -> 'Add Subscription'."
    elif device == "android":
        text = "🤖 <b>Для Android:</b>\n1. Скачай <b>v2rayNG</b>.\n2. Скопируй ссылку.\n3. В приложении: 'Группы подписок' -> '+' -> вставь ссылку и 'Обновить'."
    else:
        text = "💻 <b>Для ПК:</b>\n1. Скачай <b>v2rayN</b>.\n2. Скопируй ссылку.\n3. 'Подписка' -> 'Настройки подписки' -> Вставь ссылку -> 'Обновить'."
    await c.message.answer(text, parse_mode='HTML')

@router.callback_query(F.data == "manage_devices")
async def manage_devices(c: CallbackQuery):
    await c.answer("Функция сброса активных сессий скоро появится!", show_alert=True)

@router.callback_query(F.data == "buy_devices")
async def buy_devices_menu(c: CallbackQuery):
    b = InlineKeyboardBuilder()
    for k, t in DEVICE_TARIFFS.items():
        b.row(InlineKeyboardButton(text=f"📱 {t['name']} — {t['price']}₽", callback_data=f"buydev_{k}"))
    await c.message.answer("📱 <b>РАСШИРЕНИЕ ЛИМИТА УСТРОЙСТВ:</b>\n\nКаждое доп. устройство стоит 29₽ на всё время действия подписки.", reply_markup=b.as_markup(), parse_mode='HTML')

# --- ОПЛАТА УСТРОЙСТВ И VPN ---
@router.callback_query(F.data.startswith("buy_") | F.data.startswith("buydev_"))
async def process_pay(c: CallbackQuery):
    is_device = c.data.startswith("buydev_")
    t_key = c.data.split("_")[1] if not is_device else f"dev_{c.data.split('_')[1]}"
    tariff = DEVICE_TARIFFS[t_key] if is_device else TARIFFS[t_key]
    item_desc = f"Доп. Устройство {tariff['name']}" if is_device else f"VPN {tariff['name']}"
    
    try:
        p = Payment.create({
            "amount": {"value": str(tariff['price']), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/hfwehdhfjvorot_bot"},
            "capture": True,
            "description": item_desc,
            "metadata": {"user_id": c.from_user.id, "tariff": t_key, "type": "device" if is_device else "sub"},
            "receipt": {
                "customer": {"full_name": c.from_user.full_name, "email": "customer@vorotavpn.ru"},
                "items": [{"description": item_desc, "quantity": "1.00", "amount": {"value": str(tariff['price']), "currency": "RUB"}, "vat_code": "1", "payment_subject": "service", "payment_mode": "full_payment"}]
            }
        }, uuid.uuid4())
        b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="💰 ОПЛАТИТЬ", url=p.confirmation.confirmation_url))
        await c.message.answer(f"🛒 Заказ: {item_desc}\nСумма: {tariff['price']}₽", reply_markup=b.as_markup())
    except Exception as e:
        await c.message.answer(f"⚠️ Ошибка ЮKassa: {e}")

@router.message(F.text == "🚀 ПОДКЛЮЧИТЬ VPN")
async def connect(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if not u.subscription_end or u.subscription_end <= datetime.now():
        return await m.answer("⚠️ Подписка истекла. Пожалуйста, продлите доступ в меню 'Тарифы'.")
    
    await m.answer("📡 Подготавливаю вашу персональную ссылку...")
    if not u.vless_profile_data:
        try:
            await create_vless_profile(u.telegram_id)
        except:
            return await m.answer("❌ Ошибка генерации ключа на сервере.")
            
    sub_link = f"https://vorotavpn.ru/sub/{m.from_user.id}"
    text = (
        f"✅ <b>ВАША ССЫЛКА-ПОДПИСКА:</b>\n\n"
        f"<code>{sub_link}</code>\n\n"
        f"<b>Как подключить?</b>\n"
        f"1. Скопируйте ссылку нажатием 👆\n"
        f"2. Зайдите в приложение V2Box / v2rayNG.\n"
        f"3. Добавьте ссылку в раздел <b>Subscriptions (Подписки)</b>.\n"
        f"4. Нажмите «Обновить» (Update)!"
    )
    await m.answer(text, parse_mode='HTML')

@router.message(F.text == "🆘 ПОДДЕРЖКА")
async def support_start(m: Message, state: FSMContext):
    await m.answer("📝 Опишите вашу проблему, и администратор ответит вам здесь:")
    await state.set_state(SupportState.waiting_for_ticket)

@router.message(SupportState.waiting_for_ticket)
async def handle_ticket(m: Message, state: FSMContext, bot: Bot):
    await state.clear()
    b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="✍️ Ответить", callback_data=f"ans_{m.from_user.id}"))
    await bot.send_message(ADMIN_ID, f"📩 Тикет от @{m.from_user.username}:\n{m.text}", reply_markup=b.as_markup())
    await m.answer("✅ Отправлено поддержке.")

@router.callback_query(F.data.startswith("ans_"))
async def start_answer(c: CallbackQuery, state: FSMContext):
    await state.update_data(answer_to=c.data.split("_")[1])
    await c.message.answer("Пиши ответ пользователю:")
    await state.set_state(SupportState.waiting_for_answer)

@router.message(SupportState.waiting_for_answer)
async def send_answer(m: Message, state: FSMContext, bot: Bot):
    uid = (await state.get_data()).get("answer_to")
    await state.clear()
    await bot.send_message(uid, f"👨‍💻 <b>Ответ поддержки:</b>\n{m.text}", parse_mode='HTML')
    await m.answer("✅ Ответ отправлен пользователю.")

def setup_handlers(dp):
    dp.include_router(router)
