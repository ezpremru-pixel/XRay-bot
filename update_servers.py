from src.database import Session, Server

with Session() as db:
    # 1. Ищем нашу Австрию (которую переименовали)
    austria_server = db.query(Server).filter(Server.name == "_БелыйСписок").first()
    
    # Если вдруг уже переименовали руками, ищем по IP
    if not austria_server:
        austria_server = db.query(Server).filter(Server.ip == "2.26.73.202").first()
        
    if austria_server:
        austria_server.name = "Австрия"
        print("✅ Имя сервера успешно изменено на 'Австрия'")
        
        # 2. Магия: берем готовый шаблон от Австрии и меняем IP на московский!
        old_template = austria_server.template
        new_template = old_template.replace("2.26.73.202", "176.126.103.127")
        print(f"ℹ️ Сгенерирован новый шаблон: {new_template[:50]}...")
    else:
        print("❌ Ошибка: Австрийский сервер не найден в базе!")
        exit()

    # 3. Добавляем новый Московский Транзитный сервер
    new_server = Server(
        name="Австрия VIP (РФ-Транзит)",
        url="https://at.vorotavpn.ru:2053/HBn6F2gc5mYu09CXls",
        ip="176.126.103.127",  # Московский IP
        user="fHc928zGl6",
        password="CzCCVsc2SY",
        template=new_template, # Наш автоматически сгенерированный шаблон со всеми SNI и PBK!
        flag="🇷🇺",
        inbound_id=austria_server.inbound_id, # Копируем ID подключения
        mon_port=austria_server.mon_port      # Копируем порт мониторинга
    )
    db.add(new_server)
    db.commit()
    print("✅ Московский транзит (176.126.103.127) успешно добавлен в базу!")
