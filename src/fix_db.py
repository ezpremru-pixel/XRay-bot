from database import Session, Server
import functions

with Session() as session:
    srv = session.query(Server).filter_by(ip="37.46.19.132").first()
    if srv:
        srv.url = "http://37.46.19.132:2053/nwUUfGDVW3H2UoOGQM"
        srv.user = "fHc928zGl6"
        srv.password = "CzCCVsc2SY"
        srv.inbound_id = 1
        session.commit()
        print("✅ БАЗА ПРОБИТА: Сервер Нидерланды успешно обновлен!")
    else:
        print("❌ Ошибка: Сервер не найден в базе.")
