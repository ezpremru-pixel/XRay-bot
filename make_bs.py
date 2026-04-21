from src.database import Session, Server

# Шаблон через IP Яндекса
template_bs = "vless://uuid@81.26.185.73:443?type=tcp&encryption=none&security=reality&pbk=_sL7RnwhzzhdMkeu6rtyHtQSfIZPrxResNOZgB6-ulI&fp=chrome&sni=yahoo.com&sid=9dd8ea07&spx=%2F"

with Session() as db:
    austria = db.query(Server).filter(Server.name == "Австрия").first()
    if austria:
        austria.name = "БелыйСписок"
        austria.template = template_bs
        db.commit()
        print("✅ Австрия успешно переименована в 'БелыйСписок' и пущена через Яндекс!")
    else:
        print("❌ Сервер не найден.")
