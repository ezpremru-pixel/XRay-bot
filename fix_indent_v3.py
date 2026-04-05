import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False

for line in lines:
    if "async def process_tariff_selection" in line:
        new_lines.append(line)
        new_lines.append("    callback_data = callback.data\n")
        new_lines.append("    tariff_id = callback_data.split('_')[1]\n")
        new_lines.append("    tariff_data = await db.get_tariff(tariff_id)\n")
        new_lines.append("    if tariff_data:\n")
        new_lines.append("        amount = int(tariff_data['price'])\n")
        new_lines.append("        user_id = callback.from_user.id\n")
        new_lines.append("        pay_url = f'https://yoomoney.ru/transfer/quickpay?receiver=4100118556845340&quickpay-form=button&sum={amount}&label={user_id}'\n")
        new_lines.append("        builder = InlineKeyboardBuilder()\n")
        new_lines.append("        builder.row(InlineKeyboardButton(text=f'💳 Оплатить {amount} руб.', url=pay_url))\n")
        new_lines.append("        await callback.message.answer(f'💰 К оплате {amount} руб. за тариф \"{tariff_data[\"name\"]}\"', reply_markup=builder.as_markup())\n")
        new_lines.append("    return\n")
        skip = True
        continue
    
    if skip:
        # Пропускаем старые строки функции, пока не дойдем до следующей @ или def
        if line.strip().startswith("@") or (line.startswith("async def") and "process_tariff_selection" not in line):
            skip = False
            new_lines.append(line)
        continue
        
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("✅ Починили! Запускай бота.")
