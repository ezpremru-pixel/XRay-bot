import os
import shutil

file_path = '/var/www/vorotavpn/index.html'
backup_path = '/var/www/vorotavpn/index.html.bak'

# Делаем бэкап
shutil.copyfile(file_path, backup_path)

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. ВСТАВЛЯЕМ КНОПКУ ПОКУПКИ
btn_container = '<div class="flex flex-col sm:flex-row gap-4 justify-center items-center">'
new_btn = """<div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <button onclick="openBuyModal()" class="w-full sm:w-auto px-8 py-4 bg-green-600 hover:bg-green-500 text-white font-bold rounded-2xl shadow-lg shadow-green-600/40 transition-all transform hover:-translate-y-1 text-lg flex items-center justify-center gap-3 border border-green-500">
                    <i class="fa-solid fa-credit-card text-2xl"></i> Купить без Telegram (149₽)
                </button>"""

if "openBuyModal" not in html and btn_container in html:
    html = html.replace(btn_container, new_btn)

# 2. ВСТАВЛЯЕМ МОДАЛКУ ПЕРЕД </body>
modal_html = """
    <div id="payment-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 hidden backdrop-blur-sm px-4">
        <div class="glass-panel p-6 sm:p-8 rounded-2xl max-w-md w-full text-center relative border border-slate-600">
            <h2 class="text-2xl font-bold mb-4">🌍 Свободный интернет</h2>
            
            <div id="modal-step-1">
                <p class="mb-6 text-slate-300">Оплата тарифа на 1 месяц. Безлимитный трафик на высокой скорости.</p>
                <button id="confirm-buy-btn" onclick="processWebsiteBuy()" class="w-full py-4 bg-green-600 hover:bg-green-500 text-white font-bold rounded-xl text-lg mb-4 transition shadow-lg shadow-green-600/30">Оплатить 149 ₽</button>
                <button onclick="closeModal()" class="text-slate-400 hover:text-white transition">Отмена</button>
            </div>
            
            <div id="modal-step-check" class="hidden py-8">
                <i class="fa-solid fa-circle-notch fa-spin text-5xl text-blue-500 mb-4"></i>
                <p class="text-lg font-medium text-slate-200">Ожидаем подтверждения банка...</p>
                <p class="text-sm text-slate-400 mt-2">Обычно это занимает 5-10 секунд</p>
            </div>
            
            <div id="modal-step-success" class="hidden text-left">
                <div class="text-center mb-4">
                    <div class="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                        <i class="fa-solid fa-check text-3xl text-green-500"></i>
                    </div>
                    <h3 class="text-2xl font-bold text-green-400">Оплата успешна!</h3>
                </div>
                <p class="text-sm text-slate-300 mb-2">1. Вот твой ключ доступа (скопируй его):</p>
                <textarea id="vpn-result-key" class="w-full bg-slate-900 text-green-400 p-3 rounded-xl border border-slate-700 text-xs mb-4 font-mono focus:outline-none focus:border-green-500" rows="4" readonly></textarea>
                
                <div class="bg-yellow-500/10 border border-yellow-500/30 p-4 rounded-xl mb-4">
                    <p class="text-sm text-yellow-200"><i class="fa-solid fa-triangle-exclamation mr-1"></i> <b>ШАГ 2 (ОБЯЗАТЕЛЬНО):</b> Перейди в бота, чтобы привязать подписку. Иначе ты не сможешь её продлить!</p>
                </div>
                <a id="bot-success-link" href="#" class="block w-full py-4 bg-blue-600 hover:bg-blue-500 text-white text-center font-bold rounded-xl transition shadow-lg shadow-blue-600/30 text-lg flex items-center justify-center gap-2"><i class="fa-brands fa-telegram text-xl"></i> Перейти в Telegram</a>
            </div>
        </div>
    </div>
"""
if "id=\"payment-modal\"" not in html:
    html = html.replace('</body>', modal_html + '\n</body>')

# 3. ОБНОВЛЯЕМ СКРИПТ (Меняем старый на новый умный)
import re
new_script = """<script>
        // --- УТИЛИТЫ ДЛЯ КУКИ ---
        function setCookie(name, value, days) {
            let expires = "";
            if (days) {
                let date = new Date();
                date.setTime(date.getTime() + (days*24*60*60*1000));
                expires = "; expires=" + date.toUTCString();
            }
            document.cookie = name + "=" + (value || "")  + expires + "; path=/";
        }
        function getCookie(name) {
            let nameEQ = name + "=";
            let ca = document.cookie.split(';');
            for(let i=0;i < ca.length;i++) {
                let c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }

        // --- ЛОГИКА САЙТА И РЕФЕРАЛОВ ---
        document.addEventListener("DOMContentLoaded", function() {
            const urlParams = new URLSearchParams(window.location.search);
            const refId = urlParams.get('ref');
            
            if (refId) {
                setCookie('ref_id', refId, 30); // Запоминаем реферала на месяц!
                const links = document.querySelectorAll('.bot-link');
                links.forEach(l => {
                    l.href = `https://t.me/vorotavpn_bot?start=ref_${refId}`;
                });
            }

            // Проверка оплаты (если вернулись с ЮKassa)
            const checking = urlParams.get('checking');
            const savedPaymentId = getCookie('payment_id');
            
            if (checking && savedPaymentId) {
                document.getElementById('payment-modal').classList.remove('hidden');
                document.getElementById('modal-step-1').classList.add('hidden');
                document.getElementById('modal-step-check').classList.remove('hidden');

                const checkInterval = setInterval(async () => {
                    try {
                        const res = await fetch('/api/check', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ payment_id: savedPaymentId })
                        });
                        const data = await res.json();
                        if (data.status === 'ok') {
                            clearInterval(checkInterval);
                            document.getElementById('modal-step-check').classList.add('hidden');
                            document.getElementById('modal-step-success').classList.remove('hidden');
                            document.getElementById('vpn-result-key').value = data.key;
                            document.getElementById('bot-success-link').href = data.bot_link;
                            setCookie('payment_id', '', -1); 
                            window.history.replaceState({}, document.title, window.location.pathname);
                        }
                    } catch (e) { console.error(e); }
                }, 3000);
            }
        });

        // --- МОДАЛКА И ОПЛАТА ---
        function openBuyModal() { document.getElementById('payment-modal').classList.remove('hidden'); }
        function closeModal() { document.getElementById('payment-modal').classList.add('hidden'); }

        async function processWebsiteBuy() {
            const btn = document.getElementById('confirm-buy-btn');
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Создаем счет...';
            btn.disabled = true;
            
            const currentRef = getCookie('ref_id') || '';
            try {
                const res = await fetch('/api/buy', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ ref: currentRef })
                });
                const data = await res.json();
                if (data.url) {
                    setCookie('payment_id', data.payment_id, 1);
                    window.location.href = data.url;
                } else {
                    alert("Ошибка: " + (data.error || "Не удалось создать счет"));
                    btn.innerHTML = "Оплатить 149 ₽";
                    btn.disabled = false;
                }
            } catch (e) {
                alert("Ошибка соединения с сервером");
                btn.innerHTML = "Оплатить 149 ₽";
                btn.disabled = false;
            }
        }

        // --- Скрипт для табов ОС (твой родной) ---
        function showOS(osName) {
            document.querySelectorAll('.os-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.os-btn').forEach(el => {
                el.classList.remove('active', 'bg-blue-600', 'text-white');
            });
            document.getElementById('os-' + osName).classList.add('active');
            const activeBtn = Array.from(document.querySelectorAll('.os-btn')).find(btn => btn.getAttribute('onclick').includes(osName));
            if(activeBtn) {
                activeBtn.classList.add('active', 'bg-blue-600', 'text-white');
            }
        }
    </script>"""

html = re.sub(r'<script>.*?</script>', new_script, html, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Лендинг успешно обновлен! Дизайн сохранен, модалка и куки добавлены.")
