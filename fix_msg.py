import os

filename = 'src/handlers.py'
if os.path.exists(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Удаляем старые теги из текста сообщения
    content = content.replace("<b>", "").replace("</b>", "")
    content = content.replace("<code>", "").replace("</code>", "")
    
    # Пытаемся включить MarkdownV2 или обычный Markdown
    content = content.replace("parse_mode='HTML'", "parse_mode='Markdown'")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Текст очищен, Markdown включен!")
