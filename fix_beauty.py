import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем отображение профиля (делаем красиво через HTML)
content = content.replace("Имя профиля : {user.full_name}", "<b>Имя профиля</b>: <code>{user.full_name}</code>")
content = content.replace("Id : {user.telegram_id}", "<b>ID</b>: <code>{user.telegram_id}</code>")
content = content.replace("Подписка : {status}", "<b>Подписка</b>: {status}")
content = content.replace("Дата окончания подписки : {subscription_end}", "<b>Срок до</b>: <code>{subscription_end}</code>")

# Убираем те самые кавычки-хвосты, если они остались в тексте
content = content.replace("`", "")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
