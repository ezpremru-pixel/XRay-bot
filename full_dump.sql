PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
	id INTEGER NOT NULL, 
	telegram_id INTEGER, 
	full_name VARCHAR, 
	username VARCHAR, 
	registration_date DATETIME, 
	subscription_end DATETIME, 
	vless_profile_id VARCHAR, 
	vless_profile_data VARCHAR, 
	is_admin BOOLEAN, 
	notified BOOLEAN, device_limit INTEGER DEFAULT 3, balance FLOAT DEFAULT 0.0, referrer_id INTEGER, referral_count INTEGER DEFAULT 0, extra_device_limit INTEGER DEFAULT 0, extra_device_end DATETIME, level2_count INTEGER DEFAULT 0, earned_lvl1 FLOAT DEFAULT 0.0, earned_lvl2 FLOAT DEFAULT 0.0, is_banned BOOLEAN DEFAULT 0, custom_ref_lvl1 FLOAT DEFAULT 0.0, custom_ref_lvl2 FLOAT DEFAULT 0.0, took_test INTEGER DEFAULT 0, notified_level INTEGER DEFAULT 0, last_reminder DATETIME, payment_method_id VARCHAR, card_last4 VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (telegram_id)
);
INSERT INTO users VALUES(1,8179216822,'Vita','ezpremru','2026-04-05 22:58:35.044399','2027-07-06 02:30:40.797398',NULL,NULL,1,0,13,10.0,NULL,1,0,NULL,0,0.299999999999999988,0.0,0,36.0,6.0,0,0,'2026-04-08 22:15:57.234966',NULL,'СБП');
INSERT INTO users VALUES(2,8106847442,'Займ Сравнение','joskezxc','2026-04-06 00:35:50.254667','2026-07-14 00:35:50.253348',NULL,NULL,0,0,5,0.0,NULL,0,0,NULL,0,0.0,0.0,0,0.0,0.0,0,0,NULL,NULL,NULL);
INSERT INTO users VALUES(3,6914660184,'Виталий','joskegg','2026-04-06 01:53:50.504645','2026-05-16 05:39:28.521422',NULL,NULL,0,0,3,0.0,8179216822,0,0,NULL,0,0.0,0.0,0,0.0,0.0,0,0,NULL,NULL,NULL);
INSERT INTO users VALUES(4,930342822,'Salt_Monkey','saltm0nkey','2026-04-06 04:15:08.655259','2026-05-07 07:43:34.742145',NULL,NULL,0,1,3,0.0,NULL,0,0,NULL,0,0.0,0.0,0,0.0,0.0,0,0,NULL,NULL,NULL);
INSERT INTO users VALUES(5,5145480420,'Motandr','Motndr','2026-04-07 06:28:19.665422','2027-02-02 09:09:21.811391',NULL,NULL,0,1,3,0.0,NULL,0,0,NULL,0,0.0,0.0,0,NULL,NULL,0,0,'2026-04-08 08:59:09.827727',NULL,NULL);
INSERT INTO users VALUES(6,870401981,'Olim',NULL,'2026-04-07 18:25:38.775572','2026-04-08 20:25:48.307312',NULL,NULL,0,NULL,3,0.0,NULL,0,0,NULL,0,0.0,0.0,0,NULL,NULL,1,99,NULL,NULL,NULL);
INSERT INTO users VALUES(7,7108317408,'Андрей','aaandrey23','2026-04-08 08:29:56.644423',NULL,NULL,NULL,0,NULL,3,0.0,NULL,0,0,NULL,0,0.0,0.0,0,NULL,NULL,0,0,'2026-04-08 10:30:10.026381',NULL,NULL);
INSERT INTO users VALUES(8,5169137317,'Кит 🐋','cyber_kit01','2026-04-08 13:39:52.822153','2026-07-08 15:40:02.675090',NULL,NULL,0,NULL,3,0.0,NULL,0,0,NULL,0,0.0,0.0,0,NULL,NULL,1,0,NULL,NULL,NULL);
INSERT INTO users VALUES(9,577774404,'Жанна Корбакова','zhannetta29','2026-04-08 14:20:34.805622','2026-10-06 16:20:36.528788',NULL,NULL,0,NULL,3,0.0,NULL,0,0,NULL,0,0.0,0.0,0,NULL,NULL,1,0,NULL,NULL,NULL);
CREATE TABLE static_profiles (
	id INTEGER NOT NULL, 
	name VARCHAR, 
	vless_url VARCHAR, 
	created_at DATETIME, 
	PRIMARY KEY (id)
);
CREATE TABLE payment_history (
	id INTEGER NOT NULL, 
	telegram_id INTEGER, 
	amount FLOAT, 
	action VARCHAR, 
	date DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO payment_history VALUES(1,8179216822,1.0,'Покупка +1 устр.','2026-04-07 05:45:17.143242');
INSERT INTO payment_history VALUES(2,8179216822,1.0,'Покупка +1 устр.','2026-04-07 05:51:00.037537');
INSERT INTO payment_history VALUES(3,6914660184,1.0,'Продление на 1 дн.','2026-04-07 06:04:21.116868');
INSERT INTO payment_history VALUES(4,8179216822,1.0,'Подписка (1 дн.)','2026-04-07 09:53:39.952308');
INSERT INTO payment_history VALUES(5,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 15:45:16.552857');
INSERT INTO payment_history VALUES(6,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 15:46:53.821288');
INSERT INTO payment_history VALUES(7,8179216822,1.0,'Подписка (30 дн.)','2026-04-08 15:47:01.659028');
INSERT INTO payment_history VALUES(8,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 15:55:47.338308');
INSERT INTO payment_history VALUES(9,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 16:12:50.324590');
INSERT INTO payment_history VALUES(10,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 17:29:01.319874');
INSERT INTO payment_history VALUES(11,8179216822,1.0,'Подписка (30 дн.)','2026-04-08 17:30:00.215061');
INSERT INTO payment_history VALUES(12,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 17:53:46.648853');
INSERT INTO payment_history VALUES(13,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 19:38:28.266681');
INSERT INTO payment_history VALUES(14,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 19:55:41.213188');
INSERT INTO payment_history VALUES(15,8179216822,1.0,'Подписка ТЕСТ (30 дн.)','2026-04-08 20:08:53.254475');
CREATE TABLE withdrawals (
	id INTEGER NOT NULL, 
	telegram_id INTEGER, 
	amount FLOAT, 
	method VARCHAR, 
	details VARCHAR, 
	status VARCHAR, 
	date DATETIME, reject_reason VARCHAR, 
	PRIMARY KEY (id)
);
INSERT INTO withdrawals VALUES(1,8179216822,100.0,'СБП','vbh fdsfd','✅ Выполнено','2026-04-07 06:02:34.528429',NULL);
INSERT INTO withdrawals VALUES(2,8179216822,133.300000000000011,'СБП','sfdf 123123','✅ Выполнено','2026-04-07 09:22:28.230043',NULL);
CREATE TABLE servers (
	id INTEGER NOT NULL, 
	name VARCHAR, 
	ip VARCHAR, 
	port INTEGER, 
	mon_port INTEGER, 
	user VARCHAR, 
	password VARCHAR, 
	inbound_id INTEGER, 
	template VARCHAR, 
	flag VARCHAR, 
	is_active BOOLEAN, url VARCHAR, 
	PRIMARY KEY (id)
);
/****** CORRUPTION ERROR *******/
INSERT INTO servers VALUES(2,'Нидерланды','37.46.19.132',2053,8080,'fHc928zGl6','CzCCVsc2SY',1,'vless://uuid@nl.vorotaguard.ru:443?type=tcp&encryption=none&security=reality&pbk=3HzSXxMfTNrTkfdA7lk_s7BQWApjuNhBisE1BGhUEzY&fp=chrome&sni=www.microsoft.com&sid=25&spx=%2F#Нидерланд','ы🇳�',1,'��https://nl.vorotaguard.ru:2053/WKbp9UhYAf0fTV');
CREATE TABLE bot_settings (
	id INTEGER NOT NULL, 
	start_text VARCHAR, 
	start_image VARCHAR, 
	profile_image VARCHAR, 
	tariffs_image VARCHAR, 
	partner_image VARCHAR, proxy_link VARCHAR, 
	PRIMARY KEY (id)
);
/****** CORRUPTION ERROR *******/
ROLLBACK; -- due to errors
