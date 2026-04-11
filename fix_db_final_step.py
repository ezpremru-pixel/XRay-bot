import sys
sys.path.insert(0, 'src')
from database import Session, Server

with Session() as session:
    # 1. Обновляем Германию
    de = session.query(Server).filter(Server.ip.contains('2.27.50.25')).first()
    if de:
        de.url = "https://de.vorotavpn.ru:2053/hDFimH5nEPhSIzOJrt"
        de.template = "vless://uuid@de.vorotavpn.ru:443?type=tcp&encryption=none&security=reality&pbk=sD6p9GQPniAkHsZVoagiTu4oNDUkzjF0B_Ha-CqlnR8&fp=chrome&sni=dl.google.com&sid=d6df1f5a9312&spx=%2F#Германия"
        print("✅ Германия в базе обновлена.")
    
    # 2. На всякий случай проверяем Нидерланды (чтобы точно был домен)
    nl = session.query(Server).filter(Server.ip.contains('37.46.19.132')).first()
    if nl:
        nl.url = "https://nl.vorotavpn.ru:2053/WKbp9UhYAf0fTVfbzg"
        nl.template = "vless://uuid@nl.vorotavpn.ru:443?type=tcp&encryption=none&security=reality&pbk=3HzSXxMfTNrTkfdA7lk_s7BQWApjuNhBisE1BGhUEzY&fp=chrome&sni=www.microsoft.com&sid=25&spx=%2F#Нидерланды"
        print("✅ Нидерланды в базе обновлены.")
        
    session.commit()
