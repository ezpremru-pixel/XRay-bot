import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv('/root/XRay-bot/.env', override=True)

sender_email = os.environ.get("SMTP_EMAIL", "")
sender_password = os.environ.get("SMTP_PASSWORD", "")
test_to = "kulungus2619@yandex.ru"

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
        <div style="max-width: 650px; margin: 0 auto; padding-top: 10px;">
            
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #60a5fa; font-size: 32px; margin: 0; font-weight: 900; letter-spacing: -1px;">⛩ VOROTA ⛩</h1>
                <p style="color: #94a3b8; font-size: 16px; margin-top: 5px;">Управление подпиской</p>
            </div>

            <div style="background-color: #1e293b; border: 1px solid rgba(59,130,246,0.3); border-radius: 20px; padding: 24px; margin-bottom: 24px;">
                <h2 style="font-size: 20px; font-weight: bold; margin-top: 0; margin-bottom: 12px; color: #f8fafc;">🔗 Ссылка-Автонастройка</h2>
                <p style="color: #94a3b8; font-size: 14px; margin-top: 0; margin-bottom: 16px;">Единая ссылка для всех приложений. Она сама загрузит и будет обновлять список серверов.</p>
                <div style="background-color: #0f172a; border: 1px solid #334155; padding: 16px; border-radius: 12px; font-family: monospace; font-size: 14px; color: #bfdbfe; word-break: break-all; text-align: center;">
                    {sub_link}
                </div>
            </div>

            <div style="background-color: #3f1212; border-left: 4px solid #ef4444; border-radius: 0 16px 16px 0; padding: 20px; margin-bottom: 30px;">
                <h3 style="font-size: 18px; font-weight: 900; color: #f87171; margin-top: 0; margin-bottom: 12px;">⚠️ ВАЖНО! ОТКЛЮЧИТЕ ПРОКСИ</h3>
                <p style="color: #cbd5e1; font-weight: 500; font-size: 14px; margin-top: 0; margin-bottom: 12px;">Если вы ставили прокси для Telegram, <b>рекомендуем отключить</b> их для корректной работы Telegram с VPN!</p>
                <div style="background-color: rgba(15,23,42,0.5); padding: 12px; border-radius: 8px; border: 1px solid rgba(239,68,68,0.2);">
                    <p style="color: #cbd5e1; font-size: 13px; margin: 0 0 8px 0;"><b style="color: #fff;">С компьютера:</b> Настройки → Продвинутые → Тип соединения → <b style="color: #f87171;">Отключить прокси</b></p>
                    <p style="color: #cbd5e1; font-size: 13px; margin: 0;"><b style="color: #fff;">С телефона:</b> Данные и память → Прокси → <b style="color: #f87171;">Выключить тумблер</b></p>
                </div>
            </div>

            <h2 style="font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 24px; color: #f8fafc;">Быстрая настройка</h2>

            <div style="background-color: #1e293b; border-left: 4px solid #3b82f6; border-radius: 16px; padding: 20px; margin-bottom: 16px;">
                <h3 style="font-weight: bold; font-size: 16px; margin-top: 0; margin-bottom: 8px; color: #ffffff;">🍏 iOS (iPhone / iPad)</h3>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 8px;">1. Установите <b>Hiddify</b>, <b>V2Box</b> или <b>Happ</b> из App Store.</p>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 0;">2. Скопируйте ссылку-автонастройку, откройте приложение и нажмите "+" -> "Импорт из буфера обмена".</p>
            </div>

            <div style="background-color: #1e293b; border-left: 4px solid #a855f7; border-radius: 16px; padding: 20px; margin-bottom: 16px;">
                <h3 style="font-weight: bold; font-size: 16px; margin-top: 0; margin-bottom: 8px; color: #ffffff;">🤖 Android</h3>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 8px;">1. Установите <b>Hiddify</b>, <b>v2rayTun</b> или <b>Happ</b> из Google Play.</p>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 0;">2. В приложении выберите "Новый профиль" -> "Импорт из буфера обмена" (предварительно скопировав ссылку).</p>
            </div>

            <div style="background-color: #1e293b; border-left: 4px solid #22c55e; border-radius: 16px; padding: 20px; margin-bottom: 30px;">
                <h3 style="font-weight: bold; font-size: 16px; margin-top: 0; margin-bottom: 8px; color: #ffffff;">💻 Windows / MacOS / Linux</h3>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 0;">Установите программу <b>Hiddify</b> с GitHub, перейдите во вкладку "Подписки" и вставьте вашу Ссылку-Автонастройку.</p>
            </div>

            <div style="background-color: #451a03; border-left: 4px solid #f59e0b; border-radius: 0 16px 16px 0; padding: 24px; margin-bottom: 10px;">
                <h3 style="font-size: 18px; font-weight: 900; color: #fbbf24; margin-top: 0; margin-bottom: 12px;">🤖 ПРИВЯЖИТЕ АККАУНТ</h3>
                <p style="color: #fde68a; font-weight: 500; font-size: 14px; margin-top: 0; margin-bottom: 16px;">Обязательно привяжите покупку к своему Telegram-аккаунту! Иначе вы не сможете её продлить.</p>
                <a href="{bot_link}" style="display: block; width: 100%; text-align: center; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 16px 0; border-radius: 12px; font-weight: bold; font-size: 16px;">Авторизоваться в боте</a>
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
