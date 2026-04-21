import re

file_path = 'src/site_handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Добавляем нужную библиотеку
if "from email.utils import formataddr" not in code:
    code = code.replace("from email.mime.multipart import MIMEMultipart", "from email.mime.multipart import MIMEMultipart\nfrom email.utils import formataddr")

# Меняем кривой заголовок на правильный
old_from = 'msg[\'From\'] = f"⛩ VOROTA ⛩ <{sender_email}>"'
new_from = 'msg[\'From\'] = formataddr(("⛩ VOROTA ⛩", sender_email))'

code = code.replace(old_from, new_from)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Заголовки в боевом файле успешно исправлены!")
