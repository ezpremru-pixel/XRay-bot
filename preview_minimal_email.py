import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv

# Подгружаем пароли
load_dotenv('/root/XRay-bot/.env', override=True)

sender_email = os.environ.get("SMTP_EMAIL", "")
sender_password = os.environ.get("SMTP_PASSWORD", "")
test_to = "kulungus2619@yandex.ru" # Твой ящик для теста

sub_link = "https://solk.pw/sub/7777777777"
bot_link = "https://t.me/vorotavpn_bot?start=webpay_7777777777"

try:
    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr(("⛩ VOROTA ⛩", sender_email))
    msg['To'] = test_to
    msg['Subject'] = "Ваш ключ доступа к VOROTA и инструкция!"
    
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
    print(f"✅ УСПЕХ! Проверяй ящик {test_to}")
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
