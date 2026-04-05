import os

filename = 'src/handlers.py'
if os.path.exists(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Удаляем обратные кавычки, которые окружают блок ссылок
    content = content.replace("`{text}`", "{text}")
    content = content.replace("`{links}`", "{links}")
    
    # 2. Убираем лишние звездочки из заголовков, если они остались
    content = content.replace("**🎉 Ваш VPN профиль готов!**", "🎉 <b>Ваш VPN профиль готов!</b>")
    content = content.replace("**Инструкция по подключению:**", "<b>Инструкция по подключению:</b>")
    
    # 3. Гарантируем, что везде в этом методе стоит parse_mode='HTML'
    if "connect_profile" in content:
        # Ищем блок метода и правим в нем отправку
        content = content.replace("parse_mode='Markdown'", "parse_mode='HTML'")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Текст инструкции очищен от кавычек и звездочек!")
else:
    print("❌ Файл handlers.py не найден")
