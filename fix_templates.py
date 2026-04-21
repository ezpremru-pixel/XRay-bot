from src.database import Session, Server

# Идеально рабочие шаблоны БЕЗ FLOW
template_austria = "vless://uuid@at.vorotavpn.ru:443?type=tcp&encryption=none&security=reality&pbk=_sL7RnwhzzhdMkeu6rtyHtQSfIZPrxResNOZgB6-ulI&fp=chrome&sni=yahoo.com&sid=9dd8ea07&spx=%2F"
template_moscow = "vless://uuid@176.126.103.127:443?type=tcp&encryption=none&security=reality&pbk=_sL7RnwhzzhdMkeu6rtyHtQSfIZPrxResNOZgB6-ulI&fp=chrome&sni=yahoo.com&sid=9dd8ea07&spx=%2F"

with Session() as db:
    austria = db.query(Server).filter(Server.name == "Австрия").first()
    if austria:
        austria.template = template_austria
        print("✅ Шаблон Австрии очищен и восстановлен!")

    transit = db.query(Server).filter(Server.name == "_БелыйСписок").first()
    if transit:
        transit.template = template_moscow
        print("✅ Шаблон Москвы очищен и восстановлен!")

    db.commit()
    print("🚀 База готова!")
