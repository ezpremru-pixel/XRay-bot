import os
import re

# 1. ОБНОВЛЯЕМ ДИЗАЙН ПИСЬМА (HTML-формат)
handler_path = 'src/site_handlers.py'
with open(handler_path, 'r', encoding='utf-8') as f:
    code = f.read()

new_email_func = '''def send_email_sync(to_email, sub_link, bot_link):
    sender_email = os.environ.get("SMTP_EMAIL", "")
    sender_password = os.environ.get("SMTP_PASSWORD", "")
    
    if not sender_email or not sender_password or not to_email:
        logger.warning("⚠️ Email не отправлен: не настроены SMTP_EMAIL / SMTP_PASSWORD.")
        return
        
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"⛩ VOROTA VPN ⛩ <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = "Ваш ключ доступа к VPN и инструкция!"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb;">Успешная оплата! Ваш VPN активирован 🎉</h2>
            <p>Спасибо за покупку! Вот ваш уникальный ключ доступа (ссылка-подписка):</p>
            
            <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #cbd5e1; word-break: break-all; margin-bottom: 20px;">
                <b style="font-family: monospace; font-size: 14px; color: #0f172a;">{sub_link}</b>
            </div>
            
            <h3>🛠 Как настроить за 1 минуту:</h3>
            <ol style="margin-bottom: 20px;">
                <li><b>Скачайте приложение:</b>
                    <ul>
                        <li><b>iOS (iPhone/iPad):</b> Hiddify, V2Box или Happ (в App Store)</li>
                        <li><b>Android:</b> Hiddify, v2rayTun или Happ (в Google Play)</li>
                        <li><b>ПК (Windows/Mac):</b> Hiddify</li>
                    </ul>
                </li>
                <li><b>Скопируйте</b> вашу ссылку-подписку из серого поля выше.</li>
                <li><b>Откройте приложение</b>, нажмите "+" (в правом верхнем углу) и выберите <b>"Импорт из буфера обмена"</b> (Import from Clipboard).</li>
                <li>Нажмите главную кнопку <b>Подключить</b> (или значок Play).</li>
            </ol>

            <div style="background: #fffbeb; padding: 15px; border-left: 4px solid #f59e0b; border-radius: 4px; margin-bottom: 20px;">
                <p style="margin: 0; color: #b45309;"><b>🚨 ВАЖНЫЙ ШАГ:</b><br>
                Обязательно привяжите эту покупку к своему Telegram-аккаунту! Иначе вы не сможете продлить подписку через месяц.</p>
            </div>
            
            <a href="{bot_link}" style="display: inline-block; padding: 12px 24px; background: #2AABEE; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">🤖 Привязать в Telegram</a>
            
            <p style="margin-top: 30px; font-size: 12px; color: #64748b;">
                Приятного использования!<br>
                Команда VOROTA VPN
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Подключаемся к Mail.ru (серверы VK WorkMail используют тот же smtp)
        server = smtplib.SMTP_SSL("smtp.mail.ru", 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        logger.info(f"✅ Письмо успешно отправлено на {to_email}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки Email: {e}")'''

# Аккуратно заменяем старую функцию на новую
code = re.sub(r'def send_email_sync\(.*?(?=async def api_buy)', new_email_func + '\n\n', code, flags=re.DOTALL)
with open(handler_path, 'w', encoding='utf-8') as f:
    f.write(code)

# 2. ПРОПИСЫВАЕМ ПАРОЛИ В .ENV
env_path = '.env'
try:
    with open(env_path, 'r', encoding='utf-8') as f:
        env_content = f.read()
except FileNotFoundError:
    env_content = ''

env_content = re.sub(r'^SMTP_EMAIL=.*$', '', env_content, flags=re.MULTILINE)
env_content = re.sub(r'^SMTP_PASSWORD=.*$', '', env_content, flags=re.MULTILINE)
env_content = "\n".join([line for line in env_content.split('\n') if line.strip()])

env_content += '\nSMTP_EMAIL=noreply@game-smm.ru\nSMTP_PASSWORD=fWMid2SGKCGbyGs7Imka\n'

with open(env_path, 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✅ Письма сверстаны, пароли прописаны!")
