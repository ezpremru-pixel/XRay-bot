from database import Session, Server

with Session() as session:
    servers = session.query(Server).all()
    print("\n--- ТВОИ СЕРВЕРА В БАЗЕ ---")
    for s in servers:
        print(f"ID: {s.id} | Название: '{s.name}' | Флаг: {s.flag}")
    print("---------------------------\n")
