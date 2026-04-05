import os

for filename in ['src/handlers.py', 'src/app.py']:
    if not os.path.exists(filename): continue
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Исправляем проверку в меню
    content = content.replace("user.subscription_end > datetime.utcnow()", "(user.subscription_end is not None and user.subscription_end > datetime.utcnow())")
    content = content.replace("user.subscription_end < datetime.utcnow()", "(user.subscription_end is not None and user.subscription_end < datetime.utcnow())")
    
    # Исправляем фоновую проверку подписок
    content = content.replace("time_left = user.subscription_end - datetime.utcnow()", "time_left = user.subscription_end - datetime.utcnow() if user.subscription_end is not None else __import__('datetime').timedelta(days=-1)")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
print("✅ Код успешно пропатчен!")
