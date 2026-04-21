import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Session, User, PaymentHistory
from datetime import datetime, timedelta
from functions import create_vless_profile

router = Router()

class BindState(StatesGroup):
    waiting_for_web_id = State()

# Автоматическая привязка (клик по кнопке в письме/на сайте)
@router.message(Command("start"), F.text.contains("webpay_"))
async def start_webpay(message: Message):
    web_id_str = message.text.split("webpay_")[1]
    if web_id_str.isdigit():
        await process_binding(message, int(web_id_str))

# Ручная привязка по кнопке
@router.message(F.text == "🔑 Привязать покупку с сайта")
async def ask_web_id(message: Message, state: FSMContext):
    await message.answer("Отправьте мне вашу ссылку-подписку (которую вы получили на сайте).")
    await state.set_state(BindState.waiting_for_web_id)

@router.message(BindState.waiting_for_web_id)
async def catch_web_id(message: Message, state: FSMContext):
    text = message.text
    web_id_str = text.split('/')[-1] if '/' in text else text
    web_id_str = ''.join(filter(str.isdigit, web_id_str))
    
    if not web_id_str:
        await message.answer("❌ Не удалось найти ключ. Проверьте ссылку и отправьте еще раз.")
        return
        
    await process_binding(message, int(web_id_str))
    await state.clear()

async def process_binding(message: Message, web_user_id: int):
    real_id = message.from_user.id
    if web_user_id == real_id:
        return
        
    processing_msg = await message.answer("⏳ Синхронизируем подписку...")
    
    try:
        with Session() as session:
            web_user = session.query(User).filter_by(telegram_id=web_user_id).first()
            
            # Если юзера нет ИЛИ у него стоит наша секретная метка 999 (уже синхронизирован)
            if not web_user or web_user.notified_level == 999:
                await processing_msg.edit_text("❌ Эта покупка не найдена или уже была привязана к другому Telegram-аккаунту.")
                return
            
            real_user = session.query(User).filter_by(telegram_id=real_id).first()
            now = datetime.now()
            
            # Считаем остаток дней на сайте
            delta = web_user.subscription_end - now if web_user.subscription_end and web_user.subscription_end > now else timedelta(0)
            
            if not real_user:
                real_user = User(
                    telegram_id=real_id, 
                    full_name=message.from_user.full_name,
                    subscription_end=now + delta,
                    notified_level=0,
                    took_test=True
                )
                session.add(real_user)
            else:
                current_end = real_user.subscription_end if real_user.subscription_end and real_user.subscription_end > now else now
                real_user.subscription_end = current_end + delta
                
            # Ставим метку "СИНХРОНИЗИРОВАНО", но саму ссылку оставляем жить!
            web_user.notified_level = 999
            
            # Переносим чеки на основной аккаунт, чтобы работала стата
            payments = session.query(PaymentHistory).filter_by(telegram_id=web_user_id).all()
            for p in payments:
                p.telegram_id = real_id
                
            session.commit()
            
        # Убеждаемся, что у Telegram-аккаунта создан рабочий профиль
        await create_vless_profile(real_id, device_limit=3)
        
        sub_link = f"https://solk.pw/sub/{real_id}"
        web_link = f"https://solk.pw/sub/{web_user_id}"
        
        await processing_msg.edit_text(
            f"✅ <b>Покупка успешно привязана к вашему Telegram!</b>\n\n"
            f"Дни добавлены на ваш основной аккаунт.\n\n"
            f"🌐 <b>Ваша ссылка с сайта (доработает свои 30 дней):</b>\n<code>{web_link}</code>\n\n"
            f"📱 <b>Ваша постоянная Telegram-ссылка:</b>\n<code>{sub_link}</code>\n\n"
            f"<i>💡 Вы можете продолжать пользоваться ссылкой с сайта. А когда она истечет — просто скопируйте вашу постоянную Telegram-ссылку!</i>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        await processing_msg.edit_text("❌ Произошла ошибка. Напишите в поддержку.")
