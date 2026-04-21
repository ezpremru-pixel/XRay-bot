import re

file_path = '/var/www/vorotavpn/index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Удаляем кнопку "Взять Proxy"
html = re.sub(r'<a[^>]*href="/sub/proxy"[^>]*>.*?</a>', '', html, flags=re.DOTALL)

# 2. Меняем текст кнопки покупки
html = html.replace('Купить без Telegram (149₽)', 'Купить 149р на 30 дней')

# 3. Чиним иконку в 3 шаге (меняем проблемный fa-mobile-screen на 100% рабочий fa-mobile-alt)
html = html.replace('fa-mobile-screen', 'fa-mobile-alt')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Лендинг обновлен: кнопка прокси удалена, текст изменен, иконка починена!")
