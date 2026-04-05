import os

def clean_file(path):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Прямая замена проблемного блока
    content = content.replace('`{profile_data}`', '{profile_data}')
    content = content.replace('`{text}`', '{text}')
    
    # Убеждаемся, что парс-мод везде HTML для корректного отображения <b> и <code>
    content = content.replace("parse_mode='Markdown'", "parse_mode='HTML'")
    content = content.replace('parse_mode="Markdown"', "parse_mode='HTML'")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

clean_file('src/handlers.py')
print("✅ Handlers.py причесан под HTML!")
