from src.database import Session, Server

with Session() as db:
    # 1. Ищем старую Австрию и возвращаем ей родной флаг
    austria = db.query(Server).filter(Server.name == "Австрия").first()
    if austria:
        austria.flag = "🇦🇹"
        print("✅ У сервера 'Австрия' флаг исправлен на 🇦🇹")
    
    # 2. Ищем наш новый транзитный сервер и переименовываем его
    transit = db.query(Server).filter(Server.name == "Австрия VIP (РФ-Транзит)").first()
    if transit:
        transit.name = "_БелыйСписок"
        transit.flag = "🇷🇺"
        print("✅ Транзитный сервер переименован в '_БелыйСписок' с флагом 🇷🇺")
    else:
        # На случай, если скрипт запускается второй раз
        transit_check = db.query(Server).filter(Server.name == "_БелыйСписок").first()
        if transit_check:
            print("ℹ️ Транзитный сервер уже называется '_БелыйСписок'")

    db.commit()
    print("✅ База данных приведена в идеальный порядок!")
