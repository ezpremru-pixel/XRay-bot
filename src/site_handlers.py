import os
import uuid
import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from aiohttp import web
from yookassa import Payment
from datetime import datetime, timedelta
from database import Session, User, PaymentHistory, add_referral_earnings
from functions import create_vless_profile
from config import config
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv('/root/XRay-bot/.env', override=True)
logger = logging.getLogger(__name__)

def send_email_sync(to_email, sub_link, bot_link):
    sender_email = os.environ.get("SMTP_EMAIL", "")
    sender_password = os.environ.get("SMTP_PASSWORD", "")
    
    if not sender_email or not sender_password or not to_email:
        logger.warning(f"⚠️ Email не отправлен: не настроены пароли. Почта: {to_email}")
        return
        
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("⛩ VOROTA ⛩", sender_email))
        msg['To'] = to_email
        msg['Subject'] = "Ваш ключ доступа к VOROTA и инструкция!"
        
        # ДИЗАЙН 1 В 1 КАК НА САЙТЕ
        html_body = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 500px; margin: 0 auto; padding-top: 10px;">
            
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #60a5fa; font-size: 32px; margin: 0; font-weight: 900; letter-spacing: -1px;">⛩ VOROTA ⛩</h1>
                <p style="color: #94a3b8; font-size: 16px; margin-top: 5px;">Успешная оплата! Ваш доступ активирован 🎉</p>
            </div>

            <div style="background-color: #1e293b; border: 1px solid rgba(59,130,246,0.3); border-radius: 20px; padding: 24px; margin-bottom: 24px;">
                <h2 style="font-size: 20px; font-weight: bold; margin-top: 0; margin-bottom: 12px; color: #60a5fa;">🔗 Ваша Ссылка-Подписка</h2>
                <p style="color: #94a3b8; font-size: 14px; margin-top: 0; margin-bottom: 16px;">Это ваш уникальный ключ. Выделите и скопируйте его:</p>
                <div style="background-color: #0f172a; border: 1px solid #334155; padding: 16px; border-radius: 12px; font-family: monospace; font-size: 15px; color: #bfdbfe; word-break: break-all; text-align: center; font-weight: bold;">
                    {sub_link}
                </div>
            </div>

            <a href="{sub_link}" style="display: block; width: 100%; text-align: center; background-color: #10b981; color: #ffffff; text-decoration: none; padding: 16px 0; border-radius: 12px; font-weight: bold; font-size: 16px; margin-bottom: 16px; border: 1px solid #059669;">
                📖 Открыть инструкцию по настройке
            </a>

            <a href="{bot_link}" style="display: block; width: 100%; text-align: center; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 16px 0; border-radius: 12px; font-weight: bold; font-size: 16px; border: 1px solid #1d4ed8;">
                🤖 Привязать в Telegram (Обязательно!)
            </a>
            
        </div>
    </body>
    </html>
    """
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        server = smtplib.SMTP_SSL("smtp.mail.ru", 465, timeout=10)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logger.info(f"✅ Письмо отправлено на {to_email}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки Email на {to_email}: {e}")

async def api_buy(request):
    try:
        data = await request.json()
        ref_id = data.get('ref', '')
        user_email = data.get('email', '')
        host = request.headers.get('Host', request.host)
        domain = f"https://{host}"

        payment = Payment.create({
            "amount": {"value": "149.00", "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": f"{domain}/?checking=true"},
            "capture": True,
            "description": "Покупка VOROTA (1 месяц)",
            "receipt": {
                "customer": {"email": user_email or "info@vorotavpn.ru"},
                "items": [{"description": "VOROTA 1 месяц", "amount": {"value": "149.00", "currency": "RUB"}, "vat_code": "1", "quantity": "1.00", "payment_subject": "service", "payment_mode": "full_prepayment"}]
            },
            "metadata": {"ref_id": ref_id, "type": "web_buy", "client_email": user_email}
        }, idempotency_key=str(uuid.uuid4()))
        return web.json_response({"url": payment.confirmation.confirmation_url, "payment_id": payment.id})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_check(request):
    try:
        data = await request.json()
        payment_id = data.get('payment_id')
        payment = Payment.find_one(payment_id)
        
        if payment.status == 'succeeded':
            web_user_id = int(str(uuid.uuid5(uuid.NAMESPACE_OID, payment_id).int)[:12])
            client_uuid = await create_vless_profile(web_user_id, device_limit=3)
            
            client_email = payment.metadata.get("client_email", "Не указан")
            ref_id = payment.metadata.get("ref_id")
            
            tg_bot = Bot(token=config.BOT_TOKEN)
            
            try:
                with Session() as session:
                    user = session.query(User).filter_by(telegram_id=web_user_id).first()
                    is_first_pay = session.query(PaymentHistory).filter_by(telegram_id=web_user_id).count() == 0
                    
                    bonus_days = 7 if (is_first_pay and ref_id and ref_id.isdigit()) else 0
                    total_days = 30 + bonus_days
                    
                    if not user:
                        user = User(
                            telegram_id=web_user_id, 
                            full_name=f"Web {str(web_user_id)[:4]}", 
                            subscription_end=datetime.now() + timedelta(days=total_days), 
                            notified_level=0, 
                            took_test=True,
                            referrer_id=int(ref_id) if (ref_id and ref_id.isdigit()) else None
                        )
                        session.add(user)
                    else:
                        user.subscription_end = datetime.now() + timedelta(days=total_days)
                        if ref_id and ref_id.isdigit() and not user.referrer_id:
                            user.referrer_id = int(ref_id)
                            
                    try:
                        hist = PaymentHistory(telegram_id=web_user_id, amount=149.00, currency="RUB", payment_id=payment_id)
                        session.add(hist)
                    except: pass
                    session.commit()
                
                # --- РЕФЕРАЛКА С УВЕДОМЛЕНИЯМИ ---
                if ref_id and ref_id.isdigit():
                    try:
                        await add_referral_earnings(web_user_id, 149.00)
                        
                        with Session() as session_refs:
                            ref1 = session_refs.query(User).filter_by(telegram_id=int(ref_id)).first()
                            if ref1:
                                pct1 = float(ref1.custom_ref_lvl1) if ref1.custom_ref_lvl1 is not None else 30.0
                                gain1 = round(149.00 * (pct1 / 100), 2)
                                try:
                                    await tg_bot.send_message(ref1.telegram_id, f"🎉 <b>У вас новый реферал 1-го уровня!</b>\n\nКто-то купил подписку на сайте по вашей ссылке. Вам начислено <b>{gain1} ₽</b> ({int(pct1)}%).", parse_mode="HTML")
                                except: pass
                                
                                if ref1.referrer_id:
                                    ref2 = session_refs.query(User).filter_by(telegram_id=ref1.referrer_id).first()
                                    if ref2:
                                        pct2 = float(ref2.custom_ref_lvl2) if ref2.custom_ref_lvl2 is not None else 5.0
                                        gain2 = round(149.00 * (pct2 / 100), 2)
                                        try:
                                            await tg_bot.send_message(ref2.telegram_id, f"🎊 <b>У вас новый реферал 2-го уровня!</b>\n\nПриглашенный вашим рефералом пользователь совершил покупку. Вам начислено <b>{gain2} ₽</b> ({int(pct2)}%).", parse_mode="HTML")
                                        except: pass
                    except Exception as e:
                        logger.error(f"Ошибка рефералки и уведов: {e}")

            except Exception as e:
                logger.error(f"⚠️ Ошибка БД: {e}")
            
            try:
                admin_ids = getattr(config, 'ADMINS', [8179216822])
                for admin in admin_ids:
                    await tg_bot.send_message(admin, f"💰 <b>Новая покупка с сайта!</b>\nСумма: 149 ₽\nПочта: {client_email}\nРеферал: {ref_id if ref_id else 'Нет'}", parse_mode="HTML")
            except: pass
            finally:
                await tg_bot.session.close()
            
            sub_link = f"https://solk.pw/sub/{web_user_id}"
            bot_link = f"https://t.me/vorotavpn_bot?start=webpay_{web_user_id}"
            
            if client_email and "@" in client_email:
                asyncio.create_task(asyncio.to_thread(send_email_sync, client_email, sub_link, bot_link))
            
            return web.json_response({"status": "ok", "key": sub_link, "bot_link": bot_link})
            
        return web.json_response({"status": "pending"})
    except Exception as e:
        logger.error(f"❌ Ошибка api_check: {e}")
        return web.json_response({"error": str(e)}, status=500)

def setup_site_routes(app):
    app.router.add_post('/api/buy', app_buy)
    app.router.add_post('/api/check', api_check)
