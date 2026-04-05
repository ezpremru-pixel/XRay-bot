import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Убираем попытку импортировать конкретное имя 'Database'
# И заменяем на создание объекта, который точно есть в твоем проекте
content = content.replace("from database import Database", "from database import *")

# В твоем app.py база инициализируется как 'db_obj' или 'database'. 
# Но раз мы в тупике, давай пропишем инициализацию через глобальный поиск.
# Мы просто найдем, как называется класс базы данных в файле database.py
import re
with open('src/database.py', 'r') as db_f:
    db_content = db_f.read()
    # Ищем что-то похожее на класс управления базой
    class_match = re.search(r'class (\w+):', db_content)
    if class_match:
        db_class_name = class_match.group(1)
        # Если первый класс - это 'User', ищем следующий
        if db_class_name == 'User':
            all_classes = re.findall(r'class (\w+):', db_content)
            db_class_name = all_classes[-1] # Обычно нужный класс в конце
    else:
        db_class_name = "Database" # Заглушка

content = content.replace("db = Database()", f"db = {db_class_name}()")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Поправили импорт. Попробовали использовать класс: {db_class_name}")
