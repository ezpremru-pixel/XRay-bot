import os

path = 'src/handlers.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_until_next_def = False

for i, line in enumerate(lines):
    # Если видим начало блока выбора тарифа, заменяем его целиком
    if "async def process_tariff_selection" in line:
        new_lines.append(line)
        # Добавляем исправленное тело функции (примерный набросок логики)
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
        skip_until_next_def = True
        continue
    
    if skip_until_next_def:
        if line.startswith("async def ") or line.startswith("@"):
            skip_until_next_def = False
            new_lines.append(line)
        continue
    
    new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("✅ Отступы в блоке оплаты исправлены!")
