from src.database import Session, Server

with Session() as db:
    servers = db.query(Server).filter(Server.name.in_(["Австрия", "_БелыйСписок"])).all()
    
    for s in servers:
        if "www.microsoft.com" in s.template:
            s.template = s.template.replace("www.microsoft.com", "dl.google.com")
            print(f"✅ SNI обновлен на Google для: {s.name}")
    
    db.commit()
    print("🚀 База успешно обновлена!")
