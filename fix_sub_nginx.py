import glob
import os

for conf_file in glob.glob("/etc/nginx/sites-enabled/*"):
    with open(conf_file, "r", encoding="utf-8") as f:
        code = f.read()
    
    # Ищем блок нового домена
    if "server_name vorota-app.ru;" in code:
        block_part = code.split("server_name vorota-app.ru;")[1]
        if "location ^~ /sub/" not in block_part:
            sub_block = """    location ^~ /sub/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location ^~ /api/ {"""
            # Вставляем блок /sub/ прямо перед блоком /api/
            code = code.replace("location ^~ /api/ {", sub_block)
            
            with open(conf_file, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"✅ Маршрут /sub/ добавлен в конфигурацию!")
            os.system("nginx -s reload")
        else:
            print("⚠️ Маршрут /sub/ уже существует.")
