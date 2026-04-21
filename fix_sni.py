from src.database import Session, Server

with Session() as db:
    server = db.query(Server).filter(Server.name == "Белый список").first()
    if server:
        # Меняем yahoo.com на ya.ru в ссылке
        server.template = server.template.replace("yahoo.com", "ya.ru")
        db.commit()
        print("✅ Маскировка в боте успешно заменена на ya.ru!")
    else:
        print("❌ Сервер не найден.")
