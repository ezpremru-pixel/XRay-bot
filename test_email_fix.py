import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv('/root/XRay-bot/.env', override=True)

sender_email = os.environ.get("SMTP_EMAIL", "")
sender_password = os.environ.get("SMTP_PASSWORD", "")
test_to = "kulungus2619@yandex.ru"

msg = MIMEText("Это тестовое сообщение. Заголовки починены!", 'plain', 'utf-8')
msg['Subject'] = "Тест Почты (Исправлено)"
# 👇 ВОТ ОН, ПРАВИЛЬНЫЙ ФОРМАТ ЗАГОЛОВКА
msg['From'] = formataddr(("⛩ VOROTA ⛩", sender_email))
msg['To'] = test_to

try:
    print("⏳ Отправляем письмо с правильными заголовками...")
    server = smtplib.SMTP_SSL("smtp.mail.ru", 465, timeout=10)
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()
    print("✅ УСПЕХ! Письмо ушло. Проверь свой ящик kulungus2619@yandex.ru!")
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
