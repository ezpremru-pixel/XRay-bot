import os
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import uuid
from yookassa import Configuration, Payment
import database as db_funcs
from database import Session, User, Withdrawal, BotSettings
from functions import create_vless_profile, reset_client_ips

Configuration.account_id = '1303776'
Configuration.secret_key = 'live_0WZidMCcMnMXOwhzkB4Ux1LguAfOVzGnvr0E_dvEfas'
ADMIN_ID = 8179216822

class SupportState(StatesGroup):
    waiting_for_ticket = State()
    waiting_for_answer = State()

class WithdrawState(StatesGroup):
    waiting_for_method = State()
    waiting_for_details = State()

class AdminRejectState(StatesGroup):
    waiting_for_reason = State()

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
    "dev_test": {"name": "🧪 ТЕСТ +1 Устройство", "price": 1},
    "dev_1": {"name": "+1 Устройство", "price": 29},
    "dev_2": {"name": "+2 Устройства", "price": 58},
    "dev_3": {"name": "+3 Устройства", "price": 87},
    "dev_4": {"name": "+4 Устройства", "price": 116},
    "dev_5": {"name": "+5 Устройств", "price": 145},
}

@router.message(F.text.startswith("/start"))
async def cmd_start(m: Message, bot: Bot):
    parts = m.text.split()
    referrer_id = None
    if len(parts) > 1 and parts[1].isdigit():
        ref_candidate = int(parts[1])
        if ref_candidate != m.from_user.id:
            referrer_id = ref_candidate

    u = await db_funcs.get_user(m.from_user.id)
    if not u:
        await db_funcs.create_user(m.from_user.id, m.from_user.full_name, m.from_user.username, referrer_id=referrer_id)

    kb = [
        [KeyboardButton(text="🚀 ПОДКЛЮЧИТЬ VPN")],
        [KeyboardButton(text="💳 ТАРИФЫ"), KeyboardButton(text="🎁 ТЕСТ 24ч")],
        [KeyboardButton(text="👤 ПРОФИЛЬ"), KeyboardButton(text="🌐 ПРОКСИ")],
        [KeyboardButton(text="🤝 ПАРТНЕРКА"), KeyboardButton(text="🆘 ПОДДЕРЖКА")]
    ]
    if m.from_user.id == ADMIN_ID:
        kb.append([KeyboardButton(text="⚙️ АДМИН ПАНЕЛЬ")])

    with Session() as session:
        settings = session.query(BotSettings).first()
        start_text = settings.start_text if settings else "✨ <b>VOROTA VPN</b>\nТвой личный ключ к свободному интернету."
        start_image = settings.start_image if settings else None

    if start_image: await m.answer_photo(photo=start_image, caption=start_text, reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode='HTML')
    else: await m.answer(start_text, reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True), parse_mode='HTML')

@router.message(F.text == "🤝 ПАРТНЕРКА")
async def partner_menu(m: Message, bot: Bot):
    u = await db_funcs.get_user(m.from_user.id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={m.from_user.id}"

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💸 Вывод средств", callback_data="withdraw_funds"))
    b.row(InlineKeyboardButton(text="📜 История операций", callback_data="partner_history"))

    total_earned = u.earned_lvl1 + u.earned_lvl2
    lvl1_pct = u.custom_ref_lvl1 if u.custom_ref_lvl1 is not None else 30.0
    lvl2_pct = u.custom_ref_lvl2 if u.custom_ref_lvl2 is not None else 5.0

    text = (
        f"🤝 <b>ДВУХУРОВНЕВАЯ ПАРТНЕРСКАЯ ПРОГРАММА</b>\n\n"
        f"Приглашайте друзей и зарабатывайте реальные деньги!\n"
        f"🥇 <b>1 уровень:</b> {lvl1_pct}% от оплат.\n"
        f"🥈 <b>2 уровень:</b> {lvl2_pct}% от оплат.\n\n"
        f"📊 <b>ВАША СТАТИСТИКА:</b>\n"
        f"👥 Приглашено: <b>{u.referral_count} чел.</b> (1 ур.) | <b>{u.level2_count} чел.</b> (2 ур.)\n"
        f"💰 Заработано: <b>{total_earned:.2f} ₽</b>\n"
        f"💳 <b>Доступно к выводу: {u.balance:.2f} ₽</b>\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n<code>{ref_link}</code>"
    )
    
    with Session() as session:
        settings = session.query(BotSettings).first()
        img = settings.partner_image if settings else None

    if img: await m.answer_photo(photo=img, caption=text, reply_markup=b.as_markup(), parse_mode='HTML')
    else: await m.answer(text, reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data == "partner_history")
async def show_history(c: CallbackQuery):
    with Session() as session:
        withdrawals = session.query(Withdrawal).filter_by(telegram_id=c.from_user.id).order_by(Withdrawal.date.desc()).limit(10).all()

    if not withdrawals: return await c.answer("У вас еще нет истории выводов.", show_alert=True)

    text = "📜 <b>ПОСЛЕДНИЕ ЗАЯВКИ НА ВЫВОД:</b>\n\n"
    for w in withdrawals:
        d_str = w.date.strftime('%d.%m.%Y %H:%M')
        text += f"🗓 <b>{d_str}</b> | <b>{w.amount} ₽</b>\n💳 Способ: {w.method}\n📌 Статус: <b>{w.status}</b>\n━━━━━━━━━━━━━━━━━━\n"
    await c.message.answer(text, parse_mode='HTML')

@router.callback_query(F.data == "withdraw_funds")
async def withdraw_start(c: CallbackQuery, state: FSMContext):
    u = await db_funcs.get_user(c.from_user.id)
    if u.balance < 100: return await c.answer("Минимальная сумма для вывода 100 руб.", show_alert=True)

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="💳 Банковская карта", callback_data="w_method_card"))
    b.row(InlineKeyboardButton(text="🏦 СБП (Номер телефона)", callback_data="w_method_sbp"))
    await c.message.answer("Выберите способ вывода средств:", reply_markup=b.as_markup())
    await state.set_state(WithdrawState.waiting_for_method)

@router.callback_query(WithdrawState.waiting_for_method, F.data.startswith("w_method_"))
async def withdraw_method(c: CallbackQuery, state: FSMContext):
    method = "Карта" if c.data == "w_method_card" else "СБП"
    await state.update_data(method=method)
    await c.message.answer(f"Вы выбрали: {method}\n\nНапишите ваши реквизиты:")
    await state.set_state(WithdrawState.waiting_for_details)

@router.message(WithdrawState.waiting_for_details)
async def withdraw_details(m: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    method = data.get('method')

    with Session() as session:
        u = session.query(User).filter_by(telegram_id=m.from_user.id).first()
        amount = u.balance
        u.balance = 0.0 
        w = Withdrawal(telegram_id=u.telegram_id, amount=amount, method=method, details=m.text)
        session.add(w)
        session.commit()
    await state.clear()
    await m.answer("✅ Заявка на вывод создана и отправлена администратору.")
    
    # НОВОЕ: Уведомление админу в ТГ
    try:
        await bot.send_message(ADMIN_ID, f"💸 <b>НОВАЯ ЗАЯВКА НА ВЫВОД!</b>\n\n👤 Юзер: @{m.from_user.username or m.from_user.id}\n💰 Сумма: <b>{amount} ₽</b>\n💳 Способ: {method}\n📝 Реквизиты: <code>{m.text}</code>\n\n👉 Зайди в Админ-Панель -> Финансы.", parse_mode='HTML')
    except: pass

@router.message(F.text == "👤 ПРОФИЛЬ")
async def profile(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    d = u.subscription_end.strftime('%d.%m.%Y %H:%M') if u.subscription_end else "Нет"

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📖 ИНСТРУКЦИЯ", callback_data="show_instructions"))
    b.row(InlineKeyboardButton(text="📱 Докупить устройства", callback_data="buy_devices"))
    b.row(InlineKeyboardButton(text="🗑 Сброс устройств", callback_data="reset_devices"))

    text = f"👤 <b>ВАШ ПРОФИЛЬ</b>\n━━━━━━━━━━━━━━━━━━\n🆔 ID: <code>{m.from_user.id}</code>\n📅 Подписка до: <b>{d}</b>\n\n📱 <b>Устройства (Лимит): {u.device_limit}</b>"
    
    with Session() as session:
        settings = session.query(BotSettings).first()
        img = settings.profile_image if settings else None

    if img: await m.answer_photo(photo=img, caption=text, reply_markup=b.as_markup(), parse_mode='HTML')
    else: await m.answer(text, reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data == "reset_devices")
async def do_reset_devices(c: CallbackQuery):
    await c.answer("Сбрасываю активные сессии...", show_alert=False)
    success = await reset_client_ips(c.from_user.id)
    if success: await c.message.answer("✅ <b>Устройства успешно сброшены!</b>", parse_mode='HTML')
    else: await c.message.answer("⚠️ Ошибка сброса.")

@router.message(F.text == "🌐 ПРОКСИ")
async def free_proxy(m: Message):
    with Session() as session:
        settings = session.query(BotSettings).first()
        proxy_url = settings.proxy_link if settings and settings.proxy_link else "https://t.me/proxy"
        
    b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="👉 ПОДКЛЮЧИТЬ ПРОКСИ", url=proxy_url))
    await m.answer("🌐 <b>БЕСПЛАТНЫЙ ПРОКСИ ДЛЯ TELEGRAM</b>\n\nЖми на кнопку ниже.", reply_markup=b.as_markup(), parse_mode='HTML')

@router.message(F.text == "🎁 ТЕСТ 24ч")
async def gift_test(m: Message):
    with Session() as session:
        u_db = session.query(User).filter_by(telegram_id=m.from_user.id).first()
        if not u_db or u_db.subscription_end is not None:
            return await m.answer("❌ Вы уже использовали тестовый период или ранее имели подписку.")
        u_db.subscription_end = datetime.now() + timedelta(hours=24)
        u_db.took_test = True
        session.commit()
    await m.answer("🎉 <b>Тест на 24 часа активирован!</b>\n\nЖми «🚀 ПОДКЛЮЧИТЬ VPN».", parse_mode='HTML')

@router.message(F.text == "💳 ТАРИФЫ")
async def show_tariffs(m: Message):
    b = InlineKeyboardBuilder()
    for k, t in TARIFFS.items(): b.row(InlineKeyboardButton(text=f"🔘 {t['name']} — {t['price']}₽", callback_data=f"buy_{k}"))
    text = "💳 <b>ВЫБЕРИТЕ ТАРИФ VPN:</b>"
    
    with Session() as session:
        settings = session.query(BotSettings).first()
        img = settings.tariffs_image if settings else None

    if img: await m.answer_photo(photo=img, caption=text, reply_markup=b.as_markup(), parse_mode='HTML')
    else: await m.answer(text, reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data == "buy_devices")
async def buy_devices_menu(c: CallbackQuery):
    b = InlineKeyboardBuilder()
    for k, t in DEVICE_TARIFFS.items(): b.row(InlineKeyboardButton(text=f"📱 {t['name']} — {t['price']}₽", callback_data=f"buydev_{k}"))
    await c.message.answer("📱 <b>РАСШИРЕНИЕ ЛИМИТА:</b>\n\n+1 устройство = 29₽ на всё время.", reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data.startswith("buy_") | F.data.startswith("buydev_"))
async def process_pay(c: CallbackQuery):
    is_device = c.data.startswith("buydev_")
    t_key = c.data.replace("buydev_", "") if is_device else c.data.replace("buy_", "")
    tariff = DEVICE_TARIFFS[t_key] if is_device else TARIFFS[t_key]
    item_desc = f"Доп. Устройство {tariff['name']}" if is_device else f"VPN {tariff['name']}"

    try:
        p = Payment.create({
            "amount": {"value": str(tariff['price']), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": "https://t.me/hfwehdhfjvorot_bot"},
            "capture": True, "description": item_desc,
            "metadata": {"user_id": c.from_user.id, "tariff": t_key, "type": "device" if is_device else "sub"},
            "receipt": {"customer": {"full_name": c.from_user.full_name, "email": f"customer@{os.getenv('DOMAIN', 'solk.pw')}"}, "items": [{"description": item_desc, "quantity": "1.00", "amount": {"value": str(tariff['price']), "currency": "RUB"}, "vat_code": "1", "payment_subject": "service", "payment_mode": "full_payment"}]}
        }, uuid.uuid4())
        b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="💰 ОПЛАТИТЬ", url=p.confirmation.confirmation_url))
        await c.message.answer(f"🛒 Заказ: {item_desc}\nСумма: {tariff['price']}₽", reply_markup=b.as_markup())
    except Exception as e: await c.message.answer(f"⚠️ Ошибка ЮKassa: {e}")

@router.message(F.text == "🚀 ПОДКЛЮЧИТЬ VPN")
async def connect(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    if not u.subscription_end or u.subscription_end <= datetime.now(): return await m.answer("⚠️ Подписка истекла. Зайдите в 💳 ТАРИФЫ")
    await m.answer("📡 Подготавливаю ссылку...")
    if not u.vless_profile_data: await create_vless_profile(u.telegram_id, device_limit=u.device_limit)
    await m.answer(f"✅ <b>ВАША ССЫЛКА-ПОДПИСКА:</b>\n\n<code>https://{os.getenv('DOMAIN', 'solk.pw')}/sub/{m.from_user.id}</code>\n\n<b>Как подключить?</b>\n1. Скопируйте ссылку.\n2. Добавьте в раздел <b>Subscriptions</b> (V2Box/v2rayNG).\n3. Нажмите «Обновить»!", parse_mode='HTML')

@router.callback_query(F.data == "show_instructions")
async def show_help_inline(c: CallbackQuery):
    b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="🍏 iOS", callback_data="help_ios"), InlineKeyboardButton(text="🤖 Android", callback_data="help_android")).row(InlineKeyboardButton(text="💻 PC", callback_data="help_pc"))
    await c.message.answer("👇 <b>Выберите устройство:</b>", reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data.startswith("help_"))
async def process_help(c: CallbackQuery):
    d = c.data.split("_")[1]
    t = "🍏 <b>iOS:</b> Скачай V2Box, скопируй ссылку, Configs -> + -> Add Subscription." if d == "ios" else "🤖 <b>Android:</b> Скачай v2rayNG, скопируй ссылку, Группы подписок -> + -> вставь и Обнови." if d == "android" else "💻 <b>PC:</b> Скачай v2rayN, Подписка -> Настройки подписки -> Вставь ссылку."
    await c.message.answer(t, parse_mode='HTML')

@router.message(F.text == "🆘 ПОДДЕРЖКА")
async def support_start(m: Message, state: FSMContext):
    await m.answer("📝 Опишите вашу проблему:")
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
    await m.answer("✅ Ответ отправлен.")

def setup_handlers(dp):
    dp.include_router(router)
