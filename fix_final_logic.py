import os
import re

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    # Исправляем поломанный блок оплаты (вырезаем старый мусор если он есть)
    if "amount = int(tariff_data" in line:
        continue
    if "pay_url =" in line:
        continue
    if "builder.row(InlineKeyboardButton" in line:
        continue
    
    # Ищем место, где бот создает инвойс, и меняем на кнопку
    if "await bot.send_invoice" in line:
        indent = line[:line.find("await")]
        new_lines.append(f"{indent}amount = int(tariff_data['price'])\n")
        new_lines.append(f"{indent}pay_url = f'https://yoomoney.ru/transfer/quickpay?receiver=4100118556845340&quickpay-form=button&sum={{amount}}&label={{callback.from_user.id}}'\n")
        new_lines.append(f"{indent}builder = InlineKeyboardBuilder()\n")
        new_lines.append(f"{indent}builder.row(InlineKeyboardButton(text='💳 Оплатить {amount} руб.', url=pay_url))\n")
        new_lines.append(f"{indent}await callback.message.answer(f'💰 К оплате {{amount}} руб. за тариф \"{{tariff_data[\"name\"]}}\"', reply_markup=builder.as_markup())\n")
        continue
    
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("✅ Ошибки отступов исправлены!")
