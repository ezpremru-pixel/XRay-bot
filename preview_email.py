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

print("⏳ Верстаем письмо и отправляем...")

try:
    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr(("⛩ VOROTA ⛩", sender_email))
    msg['To'] = test_to
    msg['Subject'] = "Ваш ключ доступа к VOROTA и инструкция!"
    
    # ТОТ САМЫЙ НОВЫЙ ДИЗАЙН
    html_body = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px;">
        <div style="max-width: 650px; margin: 0 auto; padding-top: 20px;">
            
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #60a5fa; font-size: 32px; margin: 0; font-weight: 900;">⛩ VOROTA ⛩</h1>
                <p style="color: #94a3b8; font-size: 16px; margin-top: 5px;">Успешная оплата! Ваш доступ активирован 🎉</p>
            </div>

            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                <tr>
                    <td width="48%" style="background-color: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 16px; text-align: center;">
                        <div style="font-size: 11px; color: #94a3b8; font-weight: bold; margin-bottom: 6px; letter-spacing: 1px; text-transform: uppercase;">Доступна до</div>
                        <div style="font-size: 16px; font-weight: bold; color: #f8fafc;">Через 30 дней</div>
                    </td>
                    <td width="4%"></td>
                    <td width="48%" style="background-color: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 16px; text-align: center;">
                        <div style="font-size: 11px; color: #94a3b8; font-weight: bold; margin-bottom: 6px; letter-spacing: 1px; text-transform: uppercase;">Лимит устройств</div>
                        <div style="font-size: 16px; font-weight: bold; color: #f8fafc;">3 шт.</div>
                    </td>
                </tr>
            </table>

            <div style="background-color: #1e293b; border: 1px solid #3b82f6; border-radius: 24px; padding: 24px; margin-bottom: 30px;">
                <h2 style="font-size: 20px; font-weight: bold; margin-top: 0; margin-bottom: 12px; color: #f8fafc;">🔗 Ссылка-Автонастройка</h2>
                <p style="color: #94a3b8; font-size: 14px; margin-top: 0; margin-bottom: 16px;">Единая ссылка для всех приложений. Она сама загрузит и будет обновлять список серверов.</p>
                <div style="background-color: #0f172a; border: 1px solid #334155; padding: 16px; border-radius: 12px; font-family: monospace; font-size: 14px; color: #bfdbfe; word-break: break-all; text-align: center;">
                    {sub_link}
                </div>
            </div>

            <div style="background-color: #450a0a; border-left: 4px solid #ef4444; border-radius: 0 24px 24px 0; padding: 24px; margin-bottom: 30px;">
                <h3 style="font-size: 18px; font-weight: 900; color: #f87171; margin-top: 0; margin-bottom: 12px;">🚨 ВАЖНО! ПРИВЯЖИТЕ АККАУНТ</h3>
                <p style="color: #cbd5e1; font-weight: 500; font-size: 14px; margin-top: 0; margin-bottom: 16px;">Обязательно привяжите эту покупку к своему Telegram-аккаунту! Иначе вы не сможете продлить подписку и управлять ей.</p>
                <a href="{bot_link}" style="display: block; width: 100%; text-align: center; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 16px 0; border-radius: 12px; font-weight: bold; font-size: 16px;">🤖 Авторизоваться в боте</a>
            </div>

            <h2 style="font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 24px; color: #f8fafc;">Быстрая настройка</h2>

            <div style="background-color: #1e293b; border-left: 4px solid #3b82f6; border-radius: 16px; padding: 20px; margin-bottom: 16px;">
                <h3 style="font-weight: bold; font-size: 16px; margin-top: 0; margin-bottom: 8px; color: #ffffff;">Шаг 1. Установка приложения</h3>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 0; line-height: 1.8;">
                    Скачайте приложение для вашего устройства:<br>
                    <b style="color: #60a5fa;">iOS:</b> Hiddify, V2Box или Happ<br>
                    <b style="color: #4ade80;">Android:</b> Hiddify, v2rayTun или Happ<br>
                    <b style="color: #a78bfa;">ПК:</b> Hiddify
                </p>
            </div>

            <div style="background-color: #1e293b; border-left: 4px solid #a78bfa; border-radius: 16px; padding: 20px; margin-bottom: 16px;">
                <h3 style="font-weight: bold; font-size: 16px; margin-top: 0; margin-bottom: 8px; color: #ffffff;">Шаг 2. Добавление подписки</h3>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 0;">Скопируйте вашу Ссылку-Автонастройку (синий блок сверху), откройте скачанное приложение, нажмите "+" и выберите "Импорт из буфера обмена".</p>
            </div>

            <div style="background-color: #1e293b; border-left: 4px solid #4ade80; border-radius: 16px; padding: 20px; margin-bottom: 16px;">
                <h3 style="font-weight: bold; font-size: 16px; margin-top: 0; margin-bottom: 8px; color: #ffffff;">Шаг 3. Подключение и использование</h3>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 0;">В главном окне нажмите большую кнопку в центре для подключения. При необходимости вы можете менять сервер в списке конфигураций.</p>
            </div>

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
