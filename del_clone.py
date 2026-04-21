from src.database import Session, Server

with Session() as db:
    bad_server = db.query(Server).filter(Server.id == 4).first()
    if bad_server:
        db.delete(bad_server)
        db.commit()
        print("✅ Глючный клон с ID 4 успешно удален!")
    else:
        print("ℹ️ Клон не найден.")
