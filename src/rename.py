from database import Session, Server

with Session() as session:
    # Берем сервер строго по его ID (это 100% безопасно)
    server = session.query(Server).get(3)
    
    if server:
        print(f"Нашли сервер: {server.flag} {server.name}")
        server.name = "БелыйСписок"
        server.flag = "🇷🇺"
        session.commit()
        print("✅ Успешно переименовали в 🇷🇺 БелыйСписок!")
    else:
        print("❌ Ошибка: Сервер с ID 3 не найден.")
