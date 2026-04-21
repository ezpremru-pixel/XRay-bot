from src.database import Session, Server

with Session() as db:
    # Ищем наш сервер по куску названия
    bs_server = db.query(Server).filter(Server.name.contains("БелыйСписок")).first()
    
    if bs_server:
        # Пишем слово "Россия", чтобы приложение само распознало страну
        bs_server.name = "Россия | Белый Список"
        db.commit()
        print("✅ Имя успешно обновлено!")
    else:
        print("❌ Сервер не найден.")
