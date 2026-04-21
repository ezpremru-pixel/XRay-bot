file_path = '/var/www/vorotavpn/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Добавляем инпут для Email
old_btn_area = """<p class="mb-6 text-slate-300">Оплата тарифа на 1 месяц. Безлимитный трафик на высокой скорости.</p>
                <button id="confirm-buy-btn" onclick="processWebsiteBuy()"""

new_btn_area = """<p class="mb-4 text-slate-300">Оплата тарифа на 1 месяц. Безлимитный трафик на высокой скорости.</p>
                <input type="email" id="buyer-email" placeholder="Ваш Email (туда придет ключ)" class="w-full bg-slate-900 text-white p-4 rounded-xl border border-slate-700 mb-4 focus:outline-none focus:border-blue-500" required>
                <button id="confirm-buy-btn" onclick="processWebsiteBuy()"""

if 'id="buyer-email"' not in html:
    html = html.replace(old_btn_area, new_btn_area)

# Обновляем JS скрипт, чтобы он отправлял Email
old_js = """const currentRef = getCookie('ref_id') || '';
            try {
                const res = await fetch('/api/buy', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ ref: currentRef })
                });"""

new_js = """const emailInput = document.getElementById('buyer-email').value;
            if (!emailInput || !emailInput.includes('@')) {
                alert('Пожалуйста, введите корректный Email!');
                document.getElementById('confirm-buy-btn').innerHTML = "Оплатить 149 ₽";
                document.getElementById('confirm-buy-btn').disabled = false;
                return;
            }
            const currentRef = getCookie('ref_id') || '';
            try {
                const res = await fetch('/api/buy', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ ref: currentRef, email: emailInput })
                });"""

if "getElementById('buyer-email').value" not in html:
    html = html.replace(old_js, new_js)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("✅ Лендинг обновлен, поле Email добавлено!")
