from src.database import Session, Server

with Session() as db:
    servers = db.query(Server).all()
    print("\n--- СПИСОК СЕРВЕРОВ В БАЗЕ ---")
    for s in servers:
        print(f"ID: {s.id} | Имя: {s.name} | URL панели: {s.url}")
    print("------------------------------\n")
