file_path = 'src/site_handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

if "load_dotenv" not in code:
    # Добавляем принудительное чтение .env в самое начало файла
    new_imports = "from dotenv import load_dotenv\nload_dotenv('/root/XRay-bot/.env', override=True)\n"
    code = new_imports + code
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print("✅ Принудительное чтение паролей добавлено!")
else:
    print("⚠️ Чтение уже было добавлено.")
