from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    full_name = Column(String)
    username = Column(String)
    registration_date = Column(DateTime, default=datetime.utcnow)
    subscription_end = Column(DateTime)
    vless_profile_id = Column(String)
    vless_profile_data = Column(String)
    is_admin = Column(Boolean, default=False)

    # Автоплатежи (ЮKassa)
    payment_method_id = Column(String, nullable=True)
    card_last4 = Column(String, nullable=True)

    notified_level = Column(Integer, default=0)
    last_reminder = Column(DateTime, nullable=True)
    took_test = Column(Boolean, default=False)

    is_banned = Column(Boolean, default=False)
    device_limit = Column(Integer, default=3)
    extra_device_limit = Column(Integer, default=0)
    extra_device_end = Column(DateTime, nullable=True)
    balance = Column(Float, default=0.0)
    referrer_id = Column(Integer, nullable=True)
    referral_count = Column(Integer, default=0)
    level2_count = Column(Integer, default=0)
    earned_lvl1 = Column(Float, default=0.0)
    earned_lvl2 = Column(Float, default=0.0)
    custom_ref_lvl1 = Column(Float, nullable=True)
    custom_ref_lvl2 = Column(Float, nullable=True)

class PaymentHistory(Base):
    __tablename__ = 'payment_history'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    amount = Column(Float)
    action = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

class Withdrawal(Base):
    __tablename__ = 'withdrawals'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    amount = Column(Float)
    method = Column(String)
    details = Column(String)
    status = Column(String, default="⏳ Ожидание")
    reject_reason = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)

class Server(Base):
    __tablename__ = 'servers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    ip = Column(String)
    port = Column(Integer, default=2053)
    mon_port = Column(Integer, default=80)
    user = Column(String)
    password = Column(String)
    inbound_id = Column(Integer, default=1)
    template = Column(String)
    flag = Column(String)
    is_active = Column(Boolean, default=True)

class BotSettings(Base):
    __tablename__ = 'bot_settings'
    id = Column(Integer, primary_key=True)
    start_text = Column(String, default="✨ <b>VOROTA VPN</b>\nТвой личный ключ к свободному интернету.")
    start_image = Column(String, default="https://dummyimage.com/800x400/1a1a1a/ffffff&text=VOROTA+VPN+MAIN")
    profile_image = Column(String, default="https://dummyimage.com/800x400/1a1a1a/ffffff&text=PROFILE")
    tariffs_image = Column(String, default="https://dummyimage.com/800x400/1a1a1a/ffffff&text=TARIFFS")
    partner_image = Column(String, default="https://dummyimage.com/800x400/1a1a1a/ffffff&text=PARTNERS")
    proxy_link = Column(String, default="https://t.me/proxy?server=prx.enotfast.net&port=443&secret=eea705ab7e6a662eee8dc1f82b59c93f8f7275747562652e7275")

engine = create_engine('sqlite:///users.db', echo=False)
Session = sessionmaker(bind=engine)

async def init_db():
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        cols = ["took_test", "notified_level"]
        for col in cols:
            try: conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT 0"))
            except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN last_reminder DATETIME"))
        except: pass
        try: conn.execute(text("ALTER TABLE withdrawals ADD COLUMN reject_reason VARCHAR"))
        except: pass
        try: conn.execute(text("ALTER TABLE bot_settings ADD COLUMN proxy_link VARCHAR"))
        except: pass
        # Новые поля для рекуррентов
        try: conn.execute(text("ALTER TABLE users ADD COLUMN payment_method_id VARCHAR"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN card_last4 VARCHAR"))
        except: pass

    with Session() as session:
        if not session.query(BotSettings).first():
            session.add(BotSettings())
            session.commit()
    logger.info("✅ Database initialized and migrated")

async def get_user(telegram_id: int):
    with Session() as session:
        return session.query(User).filter_by(telegram_id=telegram_id).first()

async def create_user(telegram_id, full_name, username=None, is_admin=False, referrer_id=None):
    with Session() as session:
        u = User(telegram_id=telegram_id, full_name=full_name, username=username, is_admin=is_admin, referrer_id=referrer_id)
        session.add(u)
        if referrer_id:
            ref1 = session.query(User).filter_by(telegram_id=referrer_id).first()
            if ref1:
                ref1.referral_count += 1
                if ref1.referrer_id:
                    ref2 = session.query(User).filter_by(telegram_id=ref1.referrer_id).first()
                    if ref2: ref2.level2_count += 1
        session.commit()
        return u

async def delete_user_profile(telegram_id: int):
    with Session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.vless_profile_data = None
            user.notified_level = 0
            session.commit()

async def get_all_users(with_subscription: bool = None):
    with Session() as session:
        query = session.query(User)
        if with_subscription is not None:
            now = datetime.utcnow()
            if with_subscription: query = query.filter(User.subscription_end > now)
            else: query = query.filter((User.subscription_end <= now) | (User.subscription_end == None))
        return query.all()
