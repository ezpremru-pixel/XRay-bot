import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import traceback

load_dotenv('/root/XRay-bot/.env', override=True)

sender_email = os.environ.get("SMTP_EMAIL", "")
sender_password = os.environ.get("SMTP_PASSWORD", "")

# 👇 ТУТ ТВОЯ ПОЧТА ДЛЯ ТЕСТА
test_to = "kulungus2619@yandex.ru" 

print(f"🔧 Пробуем отправить с: {sender_email}")
if sender_password:
    print(f"🔑 Пароль загружен: {sender_password[:3]}...{sender_password[-3:]}")
else:
    print("❌ ПАРОЛЬ НЕ НАЙДЕН В .env")

try:
    msg = MIMEText("Это тестовое сообщение от бота VOROTA", 'plain', 'utf-8')
    msg['Subject'] = "Тест Почты"
    msg['From'] = f"⛩ VOROTA ⛩ <{sender_email}>"
    msg['To'] = test_to

    print("⏳ Подключаемся к smtp.mail.ru...")
    server = smtplib.SMTP_SSL("smtp.mail.ru", 465, timeout=10)
    server.set_debuglevel(1) # Выведет весь ответ от сервера Mail.ru!
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()
    print("\n✅ УСПЕХ! Письмо ушло.")
except Exception as e:
    print("\n❌ ОШИБКА ОТПРАВКИ:")
    traceback.print_exc()
