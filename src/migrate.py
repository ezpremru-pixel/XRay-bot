import sqlite3
import os
from datetime import datetime
import sys

# Добавляем путь, чтобы Питон видел наши новые файлы базы данных
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import Session, User

OLD_DB_PATH = 'users-20260405-203848.db'

def migrate():
    print("⏳ Начинаем перенос пользователей из старой базы...")
    
    # 1. Читаем старую базу
    try:
        conn = sqlite3.connect(OLD_DB_PATH)
        cursor = conn.cursor()
        
        # Берем ID, юзернейм, баланс и самую дальнюю дату окончания ключа
        cursor.execute('''
            SELECT u.telegram_id, u.username, u.balance, MAX(k.expiry_date) as exp_date
            FROM users u
            LEFT JOIN vpn_keys k ON u.telegram_id = k.user_id
            GROUP BY u.telegram_id
        ''')
        old_users = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка при чтении старой базы: {e}")
        return

    print(f"✅ Найдено {len(old_users)} пользователей в старой базе.")

    # 2. Пишем в новую базу
    count_added = 0
    count_updated = 0
    count_subs_restored = 0
    
    now = datetime.now()

    with Session() as session:
        for row in old_users:
            t_id, uname, bal, exp_date_str = row
            
            # Превращаем строку даты в объект datetime Питона
            exp_date = None
            if exp_date_str:
                try:
                    # Отрезаем миллисекунды, если они есть (оставляем первые 19 символов: YYYY-MM-DD HH:MM:SS)
                    exp_date = datetime.strptime(exp_date_str[:19], '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(f"⚠️ Ошибка формата даты у {t_id}: {exp_date_str}")

            # Ищем юзера в новой базе
            user = session.query(User).filter_by(telegram_id=t_id).first()
            
            if not user:
                # Юзера нет - создаем
                user = User(
                    telegram_id=t_id, 
                    username=uname, 
                    full_name=uname or f"User {t_id}", 
                    balance=bal or 0.0
                )
                session.add(user)
                count_added += 1
            else:
                # Юзер есть - плюсуем баланс, если он был в старой базе
                if bal and bal > 0:
                    user.balance += bal
                count_updated += 1

            # Восстанавливаем подписку, если она еще активна
            if exp_date and exp_date > now:
                # Если в новой базе подписки нет, или она заканчивается раньше, чем в старой
                if not user.subscription_end or exp_date > user.subscription_end:
                    user.subscription_end = exp_date
                    # Выдаем сразу 3 устройства по умолчанию
                    user.device_limit = max(user.device_limit or 3, 3) 
                    count_subs_restored += 1

        session.commit()
        
    print("\n🎉 МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print(f"👤 Новых пользователей добавлено: {count_added}")
    print(f"🔄 Существующих обновлено: {count_updated}")
    print(f"🎁 Активных подписок восстановлено: {count_subs_restored}")
    print("-------------------------------------------------")
    print("⚠️ Обязательно перезапустите бота, чтобы изменения применились на 100%.")

if __name__ == "__main__":
    migrate()
