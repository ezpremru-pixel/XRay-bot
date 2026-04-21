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
    msg['Subject'] = "Ваш ключ доступа к VOROTA и подробная инструкция!"
    
    html_body = f"""
    <html>
    <body style="font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 10px;">
        <div style="max-width: 650px; margin: 0 auto; padding-top: 10px;">
            
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #60a5fa; font-size: 32px; margin: 0; font-weight: 900; letter-spacing: -1px;">⛩ VOROTA ⛩</h1>
                <p style="color: #94a3b8; font-size: 16px; margin-top: 5px;">Успешная оплата! Ваш доступ активирован 🎉</p>
            </div>

            <div style="background-color: #1e293b; border: 1px solid rgba(59,130,246,0.3); border-radius: 20px; padding: 24px; margin-bottom: 24px;">
                <h2 style="font-size: 20px; font-weight: bold; margin-top: 0; margin-bottom: 12px; color: #60a5fa;">🔗 Ссылка-Автонастройка</h2>
                <p style="color: #94a3b8; font-size: 14px; margin-top: 0; margin-bottom: 16px;">Единая ссылка для всех приложений. Она сама загрузит и будет обновлять список серверов. Выделите и скопируйте её:</p>
                <div style="background-color: #0f172a; border: 1px solid #334155; padding: 16px; border-radius: 12px; font-family: monospace; font-size: 15px; color: #bfdbfe; word-break: break-all; text-align: center; font-weight: bold;">
                    {sub_link}
                </div>
            </div>

            <div style="background-color: #451a03; border-left: 4px solid #f59e0b; border-radius: 0 16px 16px 0; padding: 20px; margin-bottom: 24px;">
                <h3 style="font-size: 18px; font-weight: 900; color: #fbbf24; margin-top: 0; margin-bottom: 12px;">🤖 ВАЖНО! ПРИВЯЖИТЕ АККАУНТ</h3>
                <p style="color: #fde68a; font-size: 14px; margin-top: 0; margin-bottom: 16px;">Обязательно привяжите покупку к своему Telegram-аккаунту! Иначе вы не сможете её продлить.</p>
                <a href="{bot_link}" style="display: block; width: 100%; text-align: center; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 16px 0; border-radius: 12px; font-weight: bold; font-size: 16px;">Привязать в Telegram</a>
            </div>

            <div style="background-color: #3f1212; border-left: 4px solid #ef4444; border-radius: 0 16px 16px 0; padding: 20px; margin-bottom: 30px;">
                <h3 style="font-size: 18px; font-weight: 900; color: #f87171; margin-top: 0; margin-bottom: 12px;">⚠️ ОТКЛЮЧИТЕ ПРОКСИ</h3>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 12px;">Если вы ставили прокси для Telegram, <b>обязательно отключите</b> их для корректной работы!</p>
                <ul style="color: #cbd5e1; font-size: 13px; margin: 0; padding-left: 20px;">
                    <li><b>С ПК:</b> Настройки → Продвинутые → Тип соединения → Отключить</li>
                    <li><b>С телефона:</b> Данные и память → Прокси → Выключить тумблер</li>
                </ul>
            </div>

            <h2 style="font-size: 26px; font-weight: bold; text-align: center; margin-bottom: 24px; color: #f8fafc;">Быстрая настройка (Инструкции)</h2>
            <p style="text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 24px;">*Почтовые сервисы могут блокировать кнопки автодобавления. Если кнопка не сработала — просто скопируйте вашу ссылку сверху и вставьте в приложение вручную.*</p>

            <div style="background-color: #1e293b; border-left: 4px solid #3b82f6; border-radius: 16px; padding: 20px; margin-bottom: 24px;">
                <h3 style="font-weight: bold; font-size: 20px; margin-top: 0; margin-bottom: 16px; color: #ffffff;">🍏 iOS (iPhone / iPad)</h3>
                
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;"><b>Шаг 1.</b> Скачайте приложение:</p>
                <div style="margin-bottom: 20px;">
                    <a href="https://apps.apple.com/us/app/hiddify-proxy-vpn/id6596777532" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">Hiddify (Рекомендуем)</a>
                    <a href="https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">V2Box</a>
                    <a href="https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">Hit Proxy</a>
                    <a href="https://apps.apple.com/us/app/happ-proxy-utility/id6504287215" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">Happ</a>
                </div>

                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;"><b>Шаг 2.</b> Авто-импорт подписки:</p>
                <div style="margin-bottom: 20px;">
                    <a href="hiddify://install-config?url={sub_link}&name=VOROTA" style="display: block; text-align: center; padding: 12px; margin-bottom: 8px; background: #4f46e5; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">➕ Добавить в Hiddify</a>
                    <a href="v2box://install-sub?url={sub_link}&name=VOROTA" style="display: block; text-align: center; padding: 12px; margin-bottom: 8px; background: #9333ea; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">➕ Добавить в V2Box</a>
                    <a href="happ://add/{sub_link}" style="display: block; text-align: center; padding: 12px; margin-bottom: 8px; background: #16a34a; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">➕ Добавить в Happ</a>
                </div>
                
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 0;"><b>Шаг 3.</b> Подключитесь, нажав огромную кнопку в центре экрана.</p>
            </div>

            <div style="background-color: #1e293b; border-left: 4px solid #10b981; border-radius: 16px; padding: 20px; margin-bottom: 24px;">
                <h3 style="font-weight: bold; font-size: 20px; margin-top: 0; margin-bottom: 16px; color: #ffffff;">🤖 Android</h3>
                
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;"><b>Шаг 1.</b> Скачайте приложение:</p>
                <div style="margin-bottom: 20px;">
                    <a href="https://play.google.com/store/apps/details?id=app.hiddify.com" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">Hiddify (Рекомендуем)</a>
                    <a href="https://play.google.com/store/apps/details?id=com.happproxy" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">Happ</a>
                    <a href="https://play.google.com/store/apps/details?id=com.v2raytun.android" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">v2rayTun</a>
                    <a href="https://play.google.com/store/apps/details?id=io.hitray.android" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">HitRay</a>
                </div>

                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;"><b>Шаг 2.</b> Авто-импорт подписки:</p>
                <div style="margin-bottom: 20px;">
                    <a href="hiddify://install-config?url={sub_link}&name=VOROTA" style="display: block; text-align: center; padding: 12px; margin-bottom: 8px; background: #4f46e5; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">➕ Добавить в Hiddify</a>
                    <a href="happ://add/{sub_link}" style="display: block; text-align: center; padding: 12px; margin-bottom: 8px; background: #16a34a; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">➕ Добавить в Happ</a>
                    <a href="v2raytun://install-sub?url={sub_link}" style="display: block; text-align: center; padding: 12px; margin-bottom: 8px; background: #2563eb; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">➕ Добавить в v2rayTun</a>
                </div>
            </div>

            <div style="background-color: #1e293b; border-left: 4px solid #a855f7; border-radius: 16px; padding: 20px; margin-bottom: 24px;">
                <h3 style="font-weight: bold; font-size: 20px; margin-top: 0; margin-bottom: 16px; color: #ffffff;">💻 Windows</h3>
                
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;"><b>Шаг 1.</b> Скачайте .exe установщик:</p>
                <div style="margin-bottom: 20px;">
                    <a href="https://github.com/hiddify/hiddify-app/releases/download/v4.1.1/Hiddify-Windows-Setup-x64.exe" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">Hiddify (.exe)</a>
                    <a href="https://github.com/mdf45/v2raytun/releases/download/v3.8.11/v2RayTun_Setup.exe" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">v2rayTun (.exe)</a>
                </div>

                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;"><b>Шаг 2.</b> Скопируйте ссылку сверху и вставьте её в разделе "Подписки" в программе.</p>
            </div>

            <div style="background-color: #1e293b; border-left: 4px solid #ec4899; border-radius: 16px; padding: 20px; margin-bottom: 24px;">
                <h3 style="font-weight: bold; font-size: 20px; margin-top: 0; margin-bottom: 16px; color: #ffffff;">🍎 MacOS</h3>
                
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;"><b>Шаг 1.</b> Скачайте образ:</p>
                <div style="margin-bottom: 20px;">
                    <a href="https://github.com/hiddify/hiddify-app/releases/download/v4.1.1/Hiddify-MacOS.dmg" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">Hiddify (.dmg)</a>
                    <a href="https://github.com/Happ-proxy/happ-desktop/releases/latest/download/Happ.macOS.universal.dmg" style="display: inline-block; padding: 8px 12px; margin: 4px; background: #334155; color: white; text-decoration: none; border-radius: 6px; font-size: 13px;">Happ (.dmg)</a>
                </div>

                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;"><b>Шаг 2.</b> Скопируйте ссылку и добавьте в приложение вручную или через кнопки (если поддерживается почтовым клиентом):</p>
                <div>
                    <a href="hiddify://install-config?url={sub_link}&name=VOROTA" style="display: inline-block; padding: 10px; margin: 4px; background: #4f46e5; color: white; text-decoration: none; border-radius: 8px; font-size: 12px;">➕ Hiddify</a>
                    <a href="happ://add/{sub_link}" style="display: inline-block; padding: 10px; margin: 4px; background: #16a34a; color: white; text-decoration: none; border-radius: 8px; font-size: 12px;">➕ Happ</a>
                </div>
            </div>

            <div style="background-color: #1e293b; border-left: 4px solid #f97316; border-radius: 16px; padding: 20px; margin-bottom: 24px;">
                <h3 style="font-weight: bold; font-size: 20px; margin-top: 0; margin-bottom: 16px; color: #ffffff;">📺 Smart TV / Linux</h3>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 8px;"><b>Для TV:</b> Найдите в Google Play <b>Hiddify</b> или <b>v2rayTun</b>. В меню выберите "Новая подписка" и вставьте ссылку-автонастройку с этой страницы.</p>
                <p style="color: #cbd5e1; font-size: 14px; margin-top: 0; margin-bottom: 0;"><b>Для Linux:</b> Скачайте <a href="https://github.com/hiddify/hiddify-next/releases/latest/download/Hiddify-Linux-x64.AppImage" style="color: #60a5fa;">Hiddify AppImage</a>, дайте права на выполнение и добавьте ссылку в подписки.</p>
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
