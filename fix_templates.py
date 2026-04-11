import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
from database import Session, Server

with Session() as session:
    # Обновляем шаблон Германии
    de = session.query(Server).filter(Server.ip.contains('2.27.50.25')).first()
    if de:
        de.template = "vless://uuid@de.vorotavpn.ru:443?type=tcp&encryption=none&security=reality&pbk=sD6p9GQPniAkHsZVoagiTu4oNDUkzjF0B_Ha-CqlnR8&fp=chrome&sni=dl.google.com&sid=d6df1f5a9312&spx=%2F#Германия"
    
    # Обновляем шаблон Нидерландов
    nl = session.query(Server).filter(Server.ip.contains('37.46.19.132')).first()
    if nl:
        nl.template = "vless://uuid@nl.vorotavpn.ru:443?type=tcp&encryption=none&security=reality&pbk=3HzSXxMfTNrTkfdA7lk_s7BQWApjuNhBisE1BGhUEzY&fp=chrome&sni=www.microsoft.com&sid=25&spx=%2F#Нидерланды"
        
    session.commit()
    print("✅ ШАБЛОНЫ В БАЗЕ ОБНОВЛЕНЫ!")
