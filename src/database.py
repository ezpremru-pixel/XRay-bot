from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, func, text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta
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
    notified = Column(Boolean, default=False)
    
    device_limit = Column(Integer, default=3)
    extra_device_limit = Column(Integer, default=0) # Сколько куплено дополнительно
    extra_device_end = Column(DateTime, nullable=True) # Когда сгорят доп. устройства
    
    balance = Column(Float, default=0.0)
    referrer_id = Column(Integer, nullable=True)
    referral_count = Column(Integer, default=0)

# НОВАЯ ТАБЛИЦА: История платежей
class PaymentHistory(Base):
    __tablename__ = 'payment_history'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    amount = Column(Float)
    action = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

engine = create_engine('sqlite:///users.db', echo=False)
Session = sessionmaker(bind=engine)

async def init_db():
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        try: conn.execute(text("ALTER TABLE users ADD COLUMN device_limit INTEGER DEFAULT 3"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN extra_device_limit INTEGER DEFAULT 0"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN extra_device_end DATETIME"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN balance FLOAT DEFAULT 0.0"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN referrer_id INTEGER"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0"))
        except: pass

async def get_user(telegram_id: int):
    with Session() as session:
        return session.query(User).filter_by(telegram_id=telegram_id).first()

async def create_user(telegram_id, full_name, username=None, is_admin=False, referrer_id=None):
    with Session() as session:
        u = User(telegram_id=telegram_id, full_name=full_name, username=username, is_admin=is_admin, referrer_id=referrer_id)
        session.add(u)
        if referrer_id:
            ref = session.query(User).filter_by(telegram_id=referrer_id).first()
            if ref: ref.referral_count += 1
        session.commit()
        return u

async def add_payment_record(telegram_id: int, amount: float, action: str):
    with Session() as session:
        rec = PaymentHistory(telegram_id=telegram_id, amount=amount, action=action)
        session.add(rec)
        session.commit()

async def get_user_payments(telegram_id: int):
    with Session() as session:
        return session.query(PaymentHistory).filter_by(telegram_id=telegram_id).order_by(PaymentHistory.date.desc()).all()

async def get_all_users():
    with Session() as session: return session.query(User).all()
