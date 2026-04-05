import os

filename = 'src/handlers.py'
if os.path.exists(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем Markdown на HTML везде
    content = content.replace("parse_mode='Markdown'", "parse_mode='HTML'")
    content = content.replace('parse_mode="Markdown"', "parse_mode='HTML'")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Handlers переведены на HTML!")
