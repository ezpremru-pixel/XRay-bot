from database import Session, Server

with Session() as session:
    # Ищем сервер, где в названии есть "Австрия"
    server = session.query(Server).filter(Server.name.like('%Австрия%')).first()
    
    if server:
        print(f"Нашли сервер: {server.flag} {server.name}")
        server.name = "БелыйСписок"
        server.flag = "🇷🇺"
        session.commit()
        print("✅ Успешно переименовали в 🇷🇺 БелыйСписок!")
    else:
        print("❌ Сервер не найден.")
