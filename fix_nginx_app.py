import glob
import os
import re

for conf_file in glob.glob("/etc/nginx/sites-enabled/*"):
    with open(conf_file, "r", encoding="utf-8") as f:
        code = f.read()
    
    if "server_name vorota-app.ru;" in code:
        # Вставляем проброс API аккуратно после location /
        new_code = re.sub(
            r'(server_name vorota-app.ru;.*?try_files \$uri \$uri/ =404;\n\s*})', 
            r'\1\n\n    location ^~ /api/ {\n        proxy_pass http://127.0.0.1:8080;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n    }', 
            code, 
            flags=re.DOTALL
        )
        if code != new_code:
            with open(conf_file, "w", encoding="utf-8") as f:
                f.write(new_code)
            print(f"✅ Маршрут добавлен в {conf_file}!")
            os.system("nginx -s reload")
        else:
            print("⚠️ Маршрут уже есть или блок не найден.")
