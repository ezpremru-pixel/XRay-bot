import sys
sys.path.insert(0, 'src')
from database import Session, Server

with Session() as session:
    nl = session.query(Server).filter(Server.ip.contains('37.46.19.132')).first()
    if nl:
        nl.url = "https://nl.vorotavpn.ru:2053/WKbp9UhYAf0fTVfbzg"
        nl.user = "fHc928zGl6"
        nl.password = "CzCCVsc2SY"
        nl.template = "vless://uuid@nl.vorotavpn.ru:443?type=tcp&encryption=none&security=reality&pbk=3HzSXxMfTNrTkfdA7lk_s7BQWApjuNhBisE1BGhUEzY&fp=chrome&sni=www.microsoft.com&sid=25&spx=%2F#xx9thium"
        session.commit()
        print("✅ БАЗА ДАННЫХ ОБНОВЛЕНА! Нидерланды теперь смотрят на новый домен.")
    else:
        print("❌ Ошибка: Сервер не найден в базе.")
