from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Создаем движок базы данных
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

def init_database():
    """Инициализирует базу данных с поддержкой формата 2025.xlsx"""
    logger.info("Initializing database...")
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    # Добавляем начальные данные для центров ЕС ОрВД
    with SessionLocal() as db:
        try:
            # Проверяем, есть ли уже данные в таблице regions
            result = db.execute(text("SELECT COUNT(*) FROM regions")).scalar()
            
            if result == 0:
                logger.info("Adding initial air traffic centers...")
                
                # Добавляем центры ЕС ОрВД
                centers = [
                    ('Тюменский', 'TYU'),
                    ('Московский', 'MSK'),
                    ('Екатеринбургский', 'EKB'),
                    ('Санкт-Петербургский', 'SPB'),
                    ('Самарский', 'SAM'),
                    ('Ростовский', 'ROV'),
                    ('Новосибирский', 'NSK'),
                    ('Хабаровский', 'KHV'),
                    ('Красноярский', 'KRS'),
                    ('Калининградский', 'KGD'),
                    ('Якутский', 'YKT'),
                    ('Магаданский', 'MAG'),
                    ('Иркутский', 'IRK'),
                    ('Симферопольский', 'SIP')
                ]
                
                for name, code in centers:
                    db.execute(
                        text("INSERT INTO regions (name, code) VALUES (:name, :code)"),
                        {"name": name, "code": code}
                    )
                
                db.commit()
                logger.info(f"Added {len(centers)} air traffic centers")
            else:
                logger.info("Air traffic centers already exist")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            db.rollback()
            raise

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()