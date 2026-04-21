import re
import os

# 1. ОБНОВЛЯЕМ APP.PY
app_path = "src/app.py"
with open(app_path, "r", encoding="utf-8") as f:
    app_code = f.read()

if "site_handlers" not in app_code:
    # Добавляем импорт
    app_code = app_code.replace("from webhook_handler import setup_webhook", "from webhook_handler import setup_webhook\nfrom site_handlers import setup_site_routes")
    
    # Добавляем вызов маршрутов
    app_code = app_code.replace("app.router.add_post('/admin/update_domain', update_domain)", "app.router.add_post('/admin/update_domain', update_domain)\n    setup_site_routes(app)")
    
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_code)
    print("✅ app.py успешно обновлен!")

# 2. ОБНОВЛЯЕМ NGINX
nginx_path = "/etc/nginx/sites-enabled/vorota" # Имя может отличаться, найдем все
import glob
for conf_file in glob.glob("/etc/nginx/sites-enabled/*"):
    with open(conf_file, "r", encoding="utf-8") as f:
        conf_code = f.read()
    
    if "location ^~ /api/" not in conf_code and "/sub/" in conf_code:
        # Добавляем проброс API туда же, где и /sub/
        api_block = """
    location ^~ /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
"""
        conf_code = conf_code.replace("location ^~ /sub/ {", api_block + "\n    location ^~ /sub/ {")
        
        with open(conf_file, "w", encoding="utf-8") as f:
            f.write(conf_code)
        print(f"✅ Nginx конфиг ({conf_file}) обновлен!")
        os.system("nginx -s reload")
