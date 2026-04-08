from database import Session, Server
with Session() as session:
    srv = session.query(Server).filter_by(ip="37.46.19.132").first()
    if srv:
        srv.url = "https://37.46.19.132:2053/nwUUfGDVW3H2UoOGQM"
        srv.inbound_id = 1
        session.commit()
        print("✅ URL успешно обновлен на HTTPS!")
