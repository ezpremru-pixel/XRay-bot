from src.database import Session, Server

# Шаблон Белого Списка (стучится на Яндекс 81.26.185.73, а маскируется под yahoo.com)
template_bs = "vless://uuid@81.26.185.73:443?type=tcp&encryption=none&security=reality&pbk=_sL7RnwhzzhdMkeu6rtyHtQSfIZPrxResNOZgB6-ulI&fp=chrome&sni=yahoo.com&sid=9dd8ea07&spx=%2F"

with Session() as db:
    # Ищем, есть ли уже сервер, или создаем новый
    bs_server = db.query(Server).filter(Server.name == "_БелыйСписок").first()
    
    if not bs_server:
        bs_server = Server(name="_БелыйСписок", template=template_bs)
        db.add(bs_server)
        print("✅ Сервер '_БелыйСписок' успешно добавлен в базу!")
    else:
        bs_server.template = template_bs
        print("✅ Шаблон сервера '_БелыйСписок' обновлен!")

    db.commit()
    print("🚀 Всё готово!")
