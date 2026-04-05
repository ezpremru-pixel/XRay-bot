import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Заменяем строку получения db на прямое создание объекта
    if "db = kwargs.get('db')" in line:
        indent = line[:line.find("db =")]
        # Мы импортируем Database прямо здесь. 
        # Если в database.py класс называется иначе, мы это поправим следующим шагом.
        new_lines.append(f"{indent}from database import Database\n")
        new_lines.append(f"{indent}db = Database()\n")
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Попробовали инициализировать базу напрямую в обработчике.")
