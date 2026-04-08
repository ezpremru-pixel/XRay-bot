import os
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
import uuid
from urllib.parse import quote
from yookassa import Configuration, Payment
import database as db_funcs
from database import Session, User, Withdrawal, BotSettings, PaymentHistory
from functions import create_vless_profile, reset_client_ips, get_real_server_stats

Configuration.account_id = '1303776'
Configuration.secret_key = 'live_0WZidMCcMnMXOwhzkB4Ux1LguAfOVzGnvr0E_dvEfas'
ADMIN_ID = 8179216822

class SupportState(StatesGroup):
    waiting_for_ticket = State()
    waiting_for_answer = State()

class WithdrawState(StatesGroup):
    waiting_for_method = State()
    waiting_for_details = State()

class AdminState(StatesGroup):
    waiting_for_db = State()

router = Router()

TARIFFS = {
    "test1m": {"name": "🧪 ТЕСТ 1 МЕСЯЦ", "price": 1},
    "1m": {"name": "💎 1 МЕСЯЦ", "price": 149},
    "2m": {"name": "💎 2 МЕСЯЦА", "price": 269},
    "3m": {"name": "💎 3 МЕСЯЦА", "price": 369},
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

@router.message(F.text.startswith("/start"))
async def cmd_start(m: Message, bot: Bot):
    parts = m.text.split()
    referrer_id = None
    if len(parts) > 1 and parts[1].startswith("ref_"):
        ref_candidate = parts[1].replace("ref_", "")
        if ref_candidate.isdigit() and int(ref_candidate) != m.from_user.id:
            referrer_id = int(ref_candidate)
    elif len(parts) > 1 and parts[1].isdigit():
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

@router.message(F.text == "⚙️ АДМИН ПАНЕЛЬ")
async def admin_panel_menu(m: Message):
    if m.from_user.id != ADMIN_ID: return
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🌐 Открыть Web-Админку", url=f"https://{os.getenv('DOMAIN', 'solk.pw')}/admin"))
    b.row(InlineKeyboardButton(text="💳 Активные привязки", callback_data="admin_bindings"))
    b.row(InlineKeyboardButton(text="📥 Выгрузить БД", callback_data="admin_download_db"))
    b.row(InlineKeyboardButton(text="📤 Загрузить БД", callback_data="admin_upload_db"))
    await m.answer("⚙️ <b>АДМИН ПАНЕЛЬ</b>\n\nУправление ботом и базой данных:", reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data == "admin_bindings")
async def show_admin_bindings(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID: return
    with Session() as session:
        users = session.query(User).filter(User.payment_method_id != None).all()

    if not users:
        return await c.answer("Нет активных автопродлений (рекуррентов).", show_alert=True)

    text = "💳 <b>АКТИВНЫЕ АВТОПРОДЛЕНИЯ:</b>\n\n"
    for u in users:
        method = u.card_last4 if u.card_last4 else "СБП/SberPay"
        if method.startswith("*"): method = f"Карта {method}"
        next_charge = u.subscription_end.strftime('%d.%m.%Y %H:%M') if u.subscription_end else "Неизвестно"
        text += f"👤 ID: <code>{u.telegram_id}</code> (@{u.username or 'нет'})\n💳 Метод: {method}\n📅 След. списание: {next_charge}\n━━━━━━━━━━━━\n"

    if len(text) > 4000: text = text[:4000] + "\n...и другие."
    await c.message.answer(text, parse_mode='HTML')
    await c.answer()

@router.callback_query(F.data == "admin_download_db")
async def admin_download_db(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID: return
    await c.message.answer_document(FSInputFile("users.db"), caption="📦 Актуальный бэкап базы данных (users.db)")
    await c.answer()

@router.callback_query(F.data == "admin_upload_db")
async def admin_upload_db(c: CallbackQuery, state: FSMContext):
    if c.from_user.id != ADMIN_ID: return
    await c.message.answer("⚠️ <b>ВНИМАНИЕ!</b>\nОтправьте мне файл <code>users.db</code>.\nТекущая база будет ПЕРЕЗАПИСАНА!", parse_mode='HTML')
    await state.set_state(AdminState.waiting_for_db)
    await c.answer()

@router.message(AdminState.waiting_for_db, F.document)
async def admin_receive_db(m: Message, state: FSMContext, bot: Bot):
    if m.from_user.id != ADMIN_ID: return
    if m.document.file_name != "users.db":
        return await m.answer("❌ Файл должен называться строго <code>users.db</code>", parse_mode='HTML')

    await bot.download(m.document, destination="users.db")
    await m.answer("✅ <b>База данных успешно загружена!</b>\nДля применения изменений перезапустите бота через консоль:\n<code>pkill -9 -f python && nohup python src/app.py > nohup.out 2>&1 &</code>", parse_mode='HTML')
    await state.clear()

@router.message(F.text == "🤝 ПАРТНЕРКА")
async def partner_menu(m: Message, bot: Bot):
    u = await db_funcs.get_user(m.from_user.id)
    bot_info = await bot.get_me()

    with Session() as session:
        settings = session.query(BotSettings).first()
        proxy_link = settings.proxy_link if settings and settings.proxy_link else "https://t.me/proxy"
        img = settings.partner_image if settings else None

    ref_link = f"https://t.me/{bot_info.username}?start=ref_{m.from_user.id}"
    web_ref_link = f"https://vorotavpn.ru/?ref={m.from_user.id}"

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
        f"💳 <b>Доступно к выводу: {u.balance:.2f} ₽</b>\n"
        f"💸 <i>(Вывод от 500 ₽ на любую банковскую карту или СБП)</i>\n"
        f"—————————————————————\n"
        f"🔗 <b>ВАШИ ССЫЛКИ ДЛЯ ПРИГЛАШЕНИЯ:</b>\n\n"
        f"🤖 <b>Бот:</b> <code>{ref_link}</code>\n"
        f"🌐 <b>Сайт:</b> <code>{web_ref_link}</code>\n"
        f"🛡 <b>Прокси:</b> <code>{proxy_link}</code>\n\n"
        f"👇 Жмите на кнопки ниже, чтобы поделиться готовым текстом с друзьями!"
    )

    share_bot_text = quote("🤖 Привет! Нашел VPN без блокировок, ютуб и инста летают. Забирай бесплатный тест 24ч!")
    share_web_text = quote("🌐 Привет! Вот сайт классного VPN, там есть бесплатный тест и прокси для разблокировки Telegram.")
    share_proxy_text = quote("🛡 Привет! Держи рабочий Proxy для Telegram, чтобы всё грузилось без VPN.")

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📢 Поделиться Ботом", url=f"https://t.me/share/url?url={quote(ref_link)}&text={share_bot_text}"))
    b.row(InlineKeyboardButton(text="📢 Поделиться Сайтом", url=f"https://t.me/share/url?url={quote(web_ref_link)}&text={share_web_text}"))
    b.row(InlineKeyboardButton(text="📢 Поделиться Прокси", url=f"https://t.me/share/url?url={quote(proxy_link)}&text={share_proxy_text}"))
    b.row(InlineKeyboardButton(text="💸 Вывод средств", callback_data="withdraw_funds"), InlineKeyboardButton(text="📜 История", callback_data="partner_history"))

    if img: await m.answer_photo(photo=img, caption=text, reply_markup=b.as_markup(), parse_mode='HTML', disable_web_page_preview=True)
    else: await m.answer(text, reply_markup=b.as_markup(), parse_mode='HTML', disable_web_page_preview=True)

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
    if u.balance < 500: return await c.answer("Минимальная сумма для вывода 500 руб.", show_alert=True)

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

    try:
        await bot.send_message(ADMIN_ID, f"💸 <b>НОВАЯ ЗАЯВКА НА ВЫВОД!</b>\n\n👤 Юзер: @{m.from_user.username or m.from_user.id}\n💰 Сумма: <b>{amount} ₽</b>\n💳 Способ: {method}\n📝 Реквизиты: <code>{m.text}</code>\n\n👉 Зайди в Админ-Панель -> Финансы.", parse_mode='HTML')
    except: pass

@router.message(F.text == "👤 ПРОФИЛЬ")
async def profile(m: Message):
    u = await db_funcs.get_user(m.from_user.id)
    d = u.subscription_end.strftime('%d.%m.%Y %H:%M') if u.subscription_end else "Нет"

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="📖 ИНСТРУКЦИЯ (По ОС)", callback_data="show_instructions"))
    b.row(InlineKeyboardButton(text="📱 Докупить устройства", callback_data="buy_devices"))
    b.row(InlineKeyboardButton(text="🗑 Сброс устройств", callback_data="reset_devices"))

    card_info = "\n\n🔄 <b>Автопродление:</b> Выключено"
    if u.payment_method_id:
        method_str = u.card_last4 if u.card_last4 else "СБП / SberPay"
        if method_str.startswith("*"):
            method_str = f"Карта {method_str}"
        card_info = f"\n\n🔄 <b>Автопродление:</b> Включено ({method_str})\n<i>(Списание происходит автоматически)</i>"
        
    b.row(InlineKeyboardButton(text="❌ Отменить подписку", callback_data="delete_card"))

    text = f"👤 <b>ВАШ ПРОФИЛЬ</b>\n━━━━━━━━━━━━━━━━━━\n🆔 ID: <code>{m.from_user.id}</code>\n📅 Подписка до: <b>{d}</b>\n\n📱 <b>Устройства (Лимит): {u.device_limit}</b>{card_info}"

    with Session() as session:
        settings = session.query(BotSettings).first()
        img = settings.profile_image if settings else None

    if img: await m.answer_photo(photo=img, caption=text, reply_markup=b.as_markup(), parse_mode='HTML')
    else: await m.answer(text, reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data == "delete_card")
async def do_delete_card(c: CallbackQuery):
    with Session() as session:
        u = session.query(User).filter_by(telegram_id=c.from_user.id).first()
        if u and u.payment_method_id:
            u.payment_method_id = None
            u.card_last4 = None
            session.commit()
            await c.answer("✅ Подписка отменена! Автопродление и привязанные методы оплаты удалены.", show_alert=True)
        else:
            await c.answer("❌ Нет привязанных карт или СБП для отвязки.", show_alert=True)

    try: await c.message.delete()
    except: pass
    await profile(c.message)

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
    text = "💳 <b>ВЫБЕРИТЕ ТАРИФ VPN:</b>\n<i>(При оплате будет подключен автоплатеж, вы сможете отключить его в Профиле)</i>"

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
        save_method = False if is_device else True 

        p = Payment.create({
            "amount": {"value": str(tariff['price']), "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": f"https://t.me/{(await c.bot.get_me()).username}"},
            "capture": True,
            "description": item_desc,
            "save_payment_method": save_method,
            "metadata": {"user_id": c.from_user.id, "tariff": t_key, "type": "device" if is_device else "sub"},
            "receipt": {
                "customer": {
                    "email": "info@vorotavpn.ru"
                },
                "items": [
                    {
                        "description": item_desc,
                        "amount": {
                            "value": str(tariff['price']),
                            "currency": "RUB"
                        },
                        "vat_code": "1",
                        "quantity": "1.00",
                        "payment_subject": "service",
                        "payment_mode": "full_prepayment"
                    }
                ]
            }
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

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🚀 Узнать скорость", callback_data="speedtest"))

    sub_link = f"https://{os.getenv('DOMAIN', 'solk.pw')}/sub/{m.from_user.id}"

    text = f"""✅ <b>ВАША ССЫЛКА-ПОДПИСКА:</b>

<code>{sub_link}</code>

<b>Как подключить?</b>
1. Скопируйте ссылку.
2. Добавьте в раздел <b>Subscriptions</b> (V2Box/v2rayNG).
3. Нажмите «Обновить»!

💡 <a href="{sub_link}">Инструкция по настройке</a>"""

    await m.answer(text, parse_mode='HTML', reply_markup=b.as_markup(), disable_web_page_preview=True)

@router.callback_query(F.data == "speedtest")
async def run_speedtest(c: CallbackQuery):
    await c.answer("Измеряю скорость и пинг до серверов...", show_alert=False)
    msg = await c.message.answer("⏳ <i>Подключаюсь к серверам...</i>", parse_mode='HTML')

    stats = await get_real_server_stats()
    if not stats:
        return await msg.edit_text("❌ Нет доступных серверов.")

    text = "🚀 <b>СКОРОСТЬ И ПИНГ СЕРВЕРОВ:</b>\n\n"
    for s in stats:
        ping = s.get('ping', 'Ошибка')
        status_icon = "🟢" if "ms" in ping else "🔴"
        text += f"{s['flag']} <b>{s['name']}</b>\n{status_icon} Пинг: <b>{ping}</b>\n\n"

    b = InlineKeyboardBuilder().row(InlineKeyboardButton(text="🔄 Обновить", callback_data="speedtest"))
    await msg.edit_text(text, parse_mode='HTML', reply_markup=b.as_markup())

@router.callback_query(F.data == "show_instructions")
async def show_help_inline(c: CallbackQuery):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🍏 iOS", callback_data="help_ios"), InlineKeyboardButton(text="🤖 Android", callback_data="help_android"))
    b.row(InlineKeyboardButton(text="💻 Windows", callback_data="help_windows"), InlineKeyboardButton(text="🍏 MacOS", callback_data="help_macos"))
    b.row(InlineKeyboardButton(text="🐧 Linux", callback_data="help_linux"), InlineKeyboardButton(text="📺 Smart TV", callback_data="help_tv"))
    await c.message.answer("👇 <b>Выберите ваше устройство для настройки:</b>", reply_markup=b.as_markup(), parse_mode='HTML')

@router.callback_query(F.data.startswith("help_"))
async def process_help(c: CallbackQuery):
    d = c.data.split("_")[1]
    b = InlineKeyboardBuilder()

    if d == "ios":
        t = "🍏 <b>Настройка для iPhone / iPad (iOS)</b>\n\n1. Установите приложение из App Store (ссылки ниже).\n2. Скопируйте вашу Ссылку-Подписку (в меню Подключить).\n3. Откройте приложение, нажмите <b>+</b> (или Новая подписка) и выберите <b>Добавить из буфера</b>.\n4. Нажмите огромную кнопку включения."
        b.row(InlineKeyboardButton(text="📥 Скачать Hiddify", url="https://apps.apple.com/us/app/hiddify-proxy-vpn/id6596777532"))
        b.row(InlineKeyboardButton(text="📥 Скачать V2Box", url="https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690"))
        b.row(InlineKeyboardButton(text="📥 Скачать Hit Proxy", url="https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973"))
        b.row(InlineKeyboardButton(text="📥 Скачать Happ", url="https://apps.apple.com/us/app/happ-proxy-utility/id6504287215"))
        b.row(InlineKeyboardButton(text="📥 Скачать NPV Tunnel", url="https://apps.apple.com/us/app/npv-tunnel/id1629465476"))
        b.row(InlineKeyboardButton(text="📥 Скачать Streisand", url="https://apps.apple.com/us/app/streisand/id6450534064"))
    elif d == "android":
        t = "🤖 <b>Настройка для Android</b>\n\n1. Установите приложение из Google Play (ссылки ниже).\n2. Скопируйте вашу Ссылку-Подписку.\n3. Откройте приложение, перейдите в <b>Новая подписка</b> и вставьте ссылку.\n4. Нажмите сохранить/обновить и подключиться."
        b.row(InlineKeyboardButton(text="📥 Скачать Hiddify", url="https://play.google.com/store/apps/details?id=app.hiddify.com"))
        b.row(InlineKeyboardButton(text="📥 Скачать Happ", url="https://play.google.com/store/apps/details?id=com.happproxy"))
        b.row(InlineKeyboardButton(text="📥 Скачать v2rayTun", url="https://play.google.com/store/apps/details?id=com.v2raytun.android"))
        b.row(InlineKeyboardButton(text="📥 Скачать HitRay", url="https://play.google.com/store/apps/details?id=io.hitray.android"))
        b.row(InlineKeyboardButton(text="📥 Скачать NapsternetV", url="https://play.google.com/store/apps/details?id=com.napsternetlabs.napsternetv&hl=en"))
    elif d == "windows":
        t = "💻 <b>Настройка для Windows PC</b>\n\n1. Скачайте программу (.exe) и установите её.\n2. Зайдите в боте в меню Подключить и скопируйте Ссылку-Подписку.\n3. Зайдите в раздел подписок в приложении и нажмите <b>Добавить</b>.\n4. Нажмите обновить и круглую кнопку включения."
        b.row(InlineKeyboardButton(text="📥 Скачать Hiddify (.exe)", url="https://github.com/hiddify/hiddify-app/releases/download/v4.1.1/Hiddify-Windows-Setup-x64.exe"))
        b.row(InlineKeyboardButton(text="📥 Скачать Happ (.exe)", url="https://github.com/Happ-proxy/happ-desktop/releases/latest/download/setup-Happ.x64.exe"))
        b.row(InlineKeyboardButton(text="📥 Скачать v2rayTun (.exe)", url="https://github.com/mdf45/v2raytun/releases/download/v3.8.11/v2RayTun_Setup.exe"))
    elif d == "macos":
        t = "🍏 <b>Настройка для MacOS</b>\n\n1. Скачайте образ (.dmg) и перенесите в папку Программы.\n2. Скопируйте Ссылку-Подписку.\n3. Откройте приложение, перейдите в подписки и вставьте ссылку.\n4. Нажмите подключиться."
        b.row(InlineKeyboardButton(text="📥 Скачать Hiddify (.dmg)", url="https://github.com/hiddify/hiddify-app/releases/download/v4.1.1/Hiddify-MacOS.dmg"))
        b.row(InlineKeyboardButton(text="📥 Скачать Happ (.dmg)", url="https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.macOS.universal.dmg"))
    elif d == "linux":
        t = "🐧 <b>Настройка для Linux</b>\n\n1. Скачайте AppImage и дайте права на выполнение (`chmod +x`).\n2. Скопируйте Ссылку-Подписку.\n3. Вставьте её в разделе подписок программы."
        b.row(InlineKeyboardButton(text="📥 Скачать Hiddify (.AppImage)", url="https://github.com/hiddify/hiddify-next/releases/latest/download/Hiddify-Linux-x64.AppImage"))
    elif d == "tv":
        t = "📺 <b>Настройка для Smart TV (Android)</b>\n\n1. В Google Play найдите Hiddify или v2rayTun.\n2. В разделе подписок добавьте вашу Ссылку-Подписку.\n3. Выберите сервер и нажмите Подключить."
        b.row(InlineKeyboardButton(text="📥 Скачать Hiddify", url="https://play.google.com/store/apps/details?id=app.hiddify.com"))

    await c.message.answer(t, reply_markup=b.as_markup(), parse_mode='HTML', disable_web_page_preview=True)

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
