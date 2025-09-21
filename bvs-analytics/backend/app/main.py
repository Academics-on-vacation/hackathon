from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import engine, Base
from .api.flights import router as flights_router

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bvs_analytics.log")
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Starting BVS Analytics API...")
    
    # Создаем таблицы в БД
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Инициализируем базовые данные
    await initialize_base_data()
    
    yield
    
    # Shutdown
    logger.info("Shutting down BVS Analytics API...")

# Создаем приложение FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(
    flights_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["flights"]
)

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "BVS Analytics API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Проверка состояния сервиса"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Внутренняя ошибка сервера",
            "error": str(exc) if settings.LOG_LEVEL == "DEBUG" else "Internal server error"
        }
    )

async def initialize_base_data():
    """Инициализация базовых данных"""
    from .core.database import SessionLocal
    from .models.flight import Region
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже регионы в БД
        existing_regions = db.query(Region).count()
        
        if existing_regions == 0:
            logger.info("Initializing base regions data...")
            
            # Базовые регионы РФ с примерными площадями
            base_regions = [
                {"name": "Московская область", "code": "MOW", "area_km2": 44329},
                {"name": "Санкт-Петербург", "code": "SPB", "area_km2": 1439},
                {"name": "Калининградская область", "code": "KGD", "area_km2": 15125},
                {"name": "Ростовская область", "code": "ROS", "area_km2": 100967},
                {"name": "Самарская область", "code": "SAM", "area_km2": 53565},
                {"name": "Свердловская область", "code": "SVE", "area_km2": 194307},
                {"name": "Тюменская область", "code": "TYU", "area_km2": 161235},
                {"name": "Новосибирская область", "code": "NSK", "area_km2": 177756},
                {"name": "Красноярский край", "code": "KRS", "area_km2": 2366797},
                {"name": "Иркутская область", "code": "IRK", "area_km2": 767900},
                {"name": "Республика Саха (Якутия)", "code": "YAK", "area_km2": 3083523},
                {"name": "Магаданская область", "code": "MAG", "area_km2": 462464},
                {"name": "Хабаровский край", "code": "KHB", "area_km2": 787633},
                {"name": "Республика Крым", "code": "CRM", "area_km2": 27000},
            ]
            
            for region_data in base_regions:
                region = Region(**region_data)
                db.add(region)
            
            db.commit()
            logger.info(f"Initialized {len(base_regions)} base regions")
        else:
            logger.info(f"Found {existing_regions} existing regions in database")
            
    except Exception as e:
        logger.error(f"Failed to initialize base data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )