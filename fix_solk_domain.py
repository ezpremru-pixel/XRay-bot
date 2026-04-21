import re

file_path = 'src/site_handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Меняем генерацию ссылки на solk.pw
code = re.sub(r'sub_link = f"https://\{host\}/sub/\{web_user_id\}"', 'sub_link = f"https://solk.pw/sub/{web_user_id}"', code)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Домен для подписок успешно изменен на solk.pw!")
