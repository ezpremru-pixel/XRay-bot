from src.database import Session, Server

# Стандартный рабочий шаблон для Австрии (вернули yahoo.com)
template_austria = "vless://uuid@at.vorotavpn.ru:443?type=tcp&encryption=none&security=reality&pbk=_sL7RnwhzzhdMkeu6rtyHtQSfIZPrxResNOZgB6-ulI&fp=chrome&sni=yahoo.com&sid=9dd8ea07&spx=%2F"

with Session() as db:
    # 1. Восстанавливаем Австрию
    austria = db.query(Server).filter(Server.name == "Австрия").first()
    if austria:
        austria.template = template_austria
        print("✅ Шаблон Австрии восстановлен (yahoo.com)!")

    # 2. Полностью удаляем сервер Белый Список
    bs_server = db.query(Server).filter(Server.name == "_БелыйСписок").first()
    if bs_server:
        db.delete(bs_server)
        print("🗑️ Сервер '_БелыйСписок' успешно удален из базы!")
    else:
        print("ℹ️ Сервер '_БелыйСписок' уже удален.")

    db.commit()
    print("🚀 База очищена и готова!")
