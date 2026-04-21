from src.database import Session, Server

with Session() as db:
    servers = db.query(Server).all()
    for s in servers:
        if "Белый" in s.name or "Россия" in s.name or "RU" in s.name:
            # Ставим чистое название
            s.name = "Белый список"
            db.commit()
            print("✅ Имя сервера идеально очищено!")
