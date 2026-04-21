from src.database import Session, Server

with Session() as db:
    server = db.query(Server).filter(Server.name == "Белый список").first()
    if server:
        # Меняем ya.ru (или yahoo) на новую маскировку
        server.template = server.template.replace("ya.ru", "storage.yandexcloud.net").replace("yahoo.com", "storage.yandexcloud.net")
        db.commit()
        print("✅ Маскировка пробития успешно обновлена!")
