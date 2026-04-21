import re

file_path = 'src/site_handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Меняем тему письма
code = code.replace(
    'msg[\'Subject\'] = "Ваш ключ доступа к VPN и инструкция!"',
    'msg[\'Subject\'] = "Ваш ключ доступа к VOROTA и инструкция!"'
)

# Новый темный HTML-дизайн 1 в 1 как на сайте
new_html_body = '''        html_body = f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; line-height: 1.6; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #60a5fa; font-size: 28px; margin: 0;">⛩ VOROTA ⛩</h1>
                    <p style="color: #94a3b8; margin-top: 5px;">Успешная оплата! Ваш доступ активирован 🎉</p>
                </div>

                <div style="background-color: #1e293b; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px;">
                    <h2 style="font-size: 18px; margin-top: 0; margin-bottom: 16px; color: #60a5fa;">🔗 Ссылка-Автонастройка</h2>
                    <p style="color: #94a3b8; font-size: 14px; margin-bottom: 16px;">Единая ссылка для всех приложений. Она сама загрузит и будет обновлять список серверов.</p>
                    
                    <div style="background-color: #0f172a; border: 1px solid #334155; padding: 16px; border-radius: 12px; font-family: monospace; font-size: 13px; color: #bfdbfe; word-break: break-all;">
                        {sub_link}
                    </div>
                </div>

                <div style="background-color: #1e293b; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; border-left: 4px solid #3b82f6;">
                    <h3 style="font-size: 16px; margin-top: 0; color: #fff;">🛠 Как настроить за 1 минуту:</h3>
                    <ol style="color: #cbd5e1; margin-bottom: 0; padding-left: 20px; font-size: 14px;">
                        <li style="margin-bottom: 10px;"><b>Скачайте приложение:</b><br>
                            <span style="color: #94a3b8; font-size: 13px;">• iOS: Hiddify, V2Box или Happ<br>
                            • Android: Hiddify, v2rayTun или Happ<br>
                            • ПК: Hiddify</span>
                        </li>
                        <li style="margin-bottom: 10px;"><b>Скопируйте</b> ссылку-подписку (из темного блока выше).</li>
                        <li style="margin-bottom: 10px;"><b>Откройте приложение</b>, нажмите "+" и выберите <b>"Импорт из буфера обмена"</b>.</li>
                        <li>Нажмите круглую кнопку <b>Подключить</b>.</li>
                    </ol>
                </div>

                <div style="background-color: #1e293b; border: 1px solid #ef4444; border-radius: 16px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #ef4444;">
                    <h3 style="font-size: 16px; color: #f87171; margin-top: 0; margin-bottom: 10px;">🚨 ВАЖНЫЙ ШАГ:</h3>
                    <p style="color: #cbd5e1; font-size: 14px; margin: 0;">Обязательно привяжите покупку к своему Telegram-аккаунту! Иначе вы не сможете её продлить в будущем.</p>
                </div>
                
                <a href="{bot_link}" style="display: block; width: 100%; text-align: center; background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 16px 0; border-radius: 12px; font-weight: bold; font-size: 16px;">🤖 Авторизоваться в боте</a>
            </div>
        </body>
        </html>
        """'''

# Вырезаем старый html_body и вставляем новый
code = re.sub(r'html_body = f"""(.*?)"""', new_html_body.strip(), code, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Темный дизайн письма успешно установлен!")
