import re

file_path = '/var/www/vorotavpn/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Меняем "Свободный интернет" на "⛩ VOROTA ⛩"
html = html.replace('🌍 Свободный интернет', '⛩ VOROTA ⛩')

# 2. Меняем "VOROTA VPN" на "VOROTA"
html = html.replace('VOROTA VPN', 'VOROTA')

# 3. Обновляем модалку (добавляем кнопку инструкции и меняем текст уведомления)
new_modal_success = """<div id="modal-step-success" class="hidden text-left">
                <div class="text-center mb-4">
                    <div class="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                        <i class="fa-solid fa-check text-3xl text-green-500"></i>
                    </div>
                    <h3 class="text-2xl font-bold text-green-400">Оплата успешна!</h3>
                </div>
                <p class="text-sm text-slate-300 mb-2">Скопируй эту ссылку-подписку:</p>
                <textarea id="vpn-result-key" class="w-full bg-slate-900 text-green-400 p-3 rounded-xl border border-slate-700 text-xs mb-4 font-mono focus:outline-none focus:border-green-500" rows="3" readonly></textarea>
                
                <a id="instruction-link" href="#" target="_blank" class="block w-full py-3 bg-slate-800 hover:bg-slate-700 text-white text-center font-bold rounded-xl transition mb-4 border border-slate-600 shadow-lg"><i class="fa-solid fa-download text-blue-400 mr-2"></i> Подключить / Инструкция</a>

                <div class="bg-blue-500/10 border border-blue-500/30 p-4 rounded-xl mb-4">
                    <p class="text-sm text-blue-200"><i class="fa-solid fa-bell mr-2"></i><b>Уведомление:</b> Как только включишь VPN и Telegram заработает — обязательно зайди в нашего бота, чтобы привязать этот аккаунт!</p>
                </div>
                <a id="bot-success-link" href="#" class="block w-full py-4 bg-blue-600 hover:bg-blue-500 text-white text-center font-bold rounded-xl transition shadow-lg shadow-blue-600/30 text-lg flex items-center justify-center gap-2"><i class="fa-brands fa-telegram text-xl"></i> Авторизоваться в боте</a>
            </div>"""

# Аккуратно вырезаем старый Шаг 3 и вставляем новый
html = re.sub(r'<div id="modal-step-success".*?(?:Перейти в Telegram|Авторизоваться в боте)</a>\s*</div>', new_modal_success, html, flags=re.DOTALL)

# 4. Обновляем JS скрипт, чтобы кнопка инструкции открывала ссылку
if "document.getElementById('instruction-link').href" not in html:
    html = html.replace(
        "document.getElementById('bot-success-link').href = data.bot_link;", 
        "document.getElementById('bot-success-link').href = data.bot_link;\n                            if(document.getElementById('instruction-link')) document.getElementById('instruction-link').href = data.key;"
    )

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Дизайн лендинга и модалки успешно обновлен!")
