import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Умный поиск базы данных среди переданных аргументов
db_logic = """
    db = kwargs.get('db') or kwargs.get('database')
    if not db:
        # Если не нашли в kwargs, попробуем вытащить из middleware через bot
        from database import User
        # В крайнем случае создаем временный объект, если в app.py он не проброшен
        from database import Database
        db = Database() 
"""

# Но так как у тебя в database.py нет класса Database (мы это видели), 
# давай просто попробуем вытащить имя из app.py автоматически.
# Самый частый вариант в таких ботах - это передача объекта прямо в polling.

with open(path, 'w', encoding='utf-8') as f:
    # Переписываем получение db в каждой функции на более гибкое
    content = content.replace("db = kwargs.get('db')", "db = kwargs.get('db') or kwargs.get('database') or kwargs.get('repo')")
    f.write(content)

print("✅ Попробовали расширить поиск базы данных (db/database/repo).")
