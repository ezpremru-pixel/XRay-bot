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
    
    # НОВЫЕ КОЛОНКИ: Устройства и Рефералка
    device_limit = Column(Integer, default=3)
    balance = Column(Float, default=0.0)
    referrer_id = Column(Integer, nullable=True)
    referral_count = Column(Integer, default=0)

class StaticProfile(Base):
    __tablename__ = 'static_profiles'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    vless_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine('sqlite:///users.db', echo=False)
Session = sessionmaker(bind=engine)

async def init_db():
    Base.metadata.create_all(engine)
    # АВТО-МИГРАЦИЯ: Добавляем колонки в старую базу без потери данных
    with engine.begin() as conn:
        try: conn.execute(text("ALTER TABLE users ADD COLUMN device_limit INTEGER DEFAULT 3"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN balance FLOAT DEFAULT 0.0"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN referrer_id INTEGER"))
        except: pass
        try: conn.execute(text("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0"))
        except: pass
    logger.info("✅ Database tables and columns initialized")

async def get_user(telegram_id: int):
    with Session() as session:
        return session.query(User).filter_by(telegram_id=telegram_id).first()

async def create_user(telegram_id: int, full_name: str, username: str = None, is_admin: bool = False, referrer_id: int = None):
    with Session() as session:
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            subscription_end=None, # При регистрации подписки еще нет!
            is_admin=is_admin,
            referrer_id=referrer_id
        )
        session.add(user)
        
        # Если есть рефовод, увеличиваем ему счетчик
        if referrer_id:
            ref_user = session.query(User).filter_by(telegram_id=referrer_id).first()
            if ref_user:
                ref_user.referral_count += 1
                
        session.commit()
        logger.info(f"✅ New user created: {telegram_id} (Ref: {referrer_id})")
        return user

async def delete_user_profile(telegram_id: int):
    with Session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.vless_profile_data = None
            user.notified = False
            session.commit()
            logger.info(f"✅ User profile deleted: {telegram_id}")

async def update_subscription(telegram_id: int, months: int):
    with Session() as session:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            now = datetime.utcnow()
            if user.subscription_end and user.subscription_end > now:
                user.subscription_end += timedelta(days=months * 30)
            else:
                user.subscription_end = now + timedelta(days=months * 30)
            user.notified = False
            session.commit()
            return True
        return False

async def get_all_users(with_subscription: bool = None):
    with Session() as session:
        query = session.query(User)
        if with_subscription is not None:
            if with_subscription:
                query = query.filter(User.subscription_end > datetime.utcnow())
            else:
                query = query.filter(User.subscription_end <= datetime.utcnow())
        return query.all()

async def create_static_profile(name: str, vless_url: str):
    with Session() as session:
        profile = StaticProfile(name=name, vless_url=vless_url)
        session.add(profile)
        session.commit()
        return profile

async def get_static_profiles():
    with Session() as session:
        return session.query(StaticProfile).all()

async def get_user_stats():
    with Session() as session:
        total = session.query(func.count(User.id)).scalar()
        with_sub = session.query(func.count(User.id)).filter(User.subscription_end > datetime.utcnow()).scalar()
        without_sub = total - with_sub
        return total, with_sub, without_sub
