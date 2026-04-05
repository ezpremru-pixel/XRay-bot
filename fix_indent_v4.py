import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False

for line in lines:
    if "async def process_tariff_selection" in line:
        new_lines.append(line)
        new_lines.append("    # Исправленная функция оплаты\n")
        new_lines.append("    tariff_id = callback.data.split('_')[1]\n")
        new_lines.append("    tariff_data = await db.get_tariff(tariff_id)\n")
        new_lines.append("    if tariff_data:\n")
        new_lines.append("        amount = int(tariff_data['price'])\n")
        new_lines.append("        pay_url = f'https://yoomoney.ru/transfer/quickpay?receiver=4100118556845340&quickpay-form=button&sum={amount}&label={callback.from_user.id}'\n")
        new_lines.append("        builder = InlineKeyboardBuilder()\n")
        new_lines.append("        builder.row(InlineKeyboardButton(text=f'💳 Оплатить {amount} руб.', url=pay_url))\n")
        new_lines.append("        await callback.message.answer(f'💰 Тариф: {tariff_data[\"name\"]}. К оплате: {amount} руб.', reply_markup=builder.as_markup())\n")
        new_lines.append("    return\n")
        skip = True
        continue
    
    if skip:
        if line.strip().startswith("@") or (line.startswith("async def") and "process_tariff_selection" not in line):
            skip = False
            new_lines.append(line)
        continue
        
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("✅ Поправили отступы. Теперь пробуй запустить!")
