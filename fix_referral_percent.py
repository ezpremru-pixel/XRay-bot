import re

file_path = 'src/site_handlers.py'
with open(file_path, 'r', encoding='utf-8') as f:
    code = f.read()

# Умная замена старой логики на динамическую (с учетом процента юзера)
old_regex = r'bonus = 149\.00 \* 0\.30.*?\(30%\)\.",\s*parse_mode="HTML"\s*\)\s*except:\s*pass'

new_logic = """# Берем персональный процент юзера из БД (если колонки нет, дефолт 30%)
                            user_percent = float(getattr(referrer, 'ref_percent', getattr(referrer, 'referral_percent', getattr(referrer, 'percent', 30))))
                            bonus = round(149.00 * (user_percent / 100.0), 2)
                            
                            try:
                                referrer.balance = float(getattr(referrer, 'balance', 0)) + bonus
                            except: pass
                            
                            try:
                                await tg_bot.send_message(
                                    int(ref_id), 
                                    f"🎉 <b>У вас новый реферал!</b>\\n\\nКто-то купил подписку на сайте по вашей ссылке. Вам начислено <b>{bonus} ₽</b> ({int(user_percent)}%).", 
                                    parse_mode="HTML"
                                )
                            except: pass"""

code = re.sub(old_regex, new_logic, code, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Динамический процент рефералки успешно встроен!")
