from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import sys
from contextlib import asynccontextmanager

from .core.config import settings
from .core.database import engine, Base, init_database
from .api.flights import router as flights_router
from .api.auth import auth as auth_router

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

current_dir = Path(__file__).parent
frontend_dist_path = current_dir.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Starting BVS Analytics API...")

    if frontend_dist_path.exists():
        logger.info(f"Frontend found at: {frontend_dist_path}")
    else:
        logger.warning(f"Frontend not found at: {frontend_dist_path}")
    # Инициализируем базу данных с поддержкой формата 2025.xlsx
    try:
        init_database()
        logger.info("Database initialized successfully with 2025.xlsx support")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

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

# ПЕРВЫМ ДЕЛОМ - подключаем API роутеры
app.include_router(
    flights_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["flights"]
)
app.include_router(
    auth_router,
    tags=["auth"]
)

# Затем - статические файлы фронтенда
if frontend_dist_path.exists():
    # Vite создает assets вместо static
    assets_path = frontend_dist_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")


# API роуты должны быть объявлены ДО catch-all роута
@app.get("/")
async def root():
    """Корневой эндпоинт - обслуживает Vue приложение"""
    if frontend_dist_path.exists():
        index_file = frontend_dist_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    # Если фронтенд не собран, показываем API информацию
    return {
        "message": "BVS Analytics API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "frontend_status": "not_built" if not frontend_dist_path.exists() else "available"
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


# ПОСЛЕДНИМ - catch-all роут для Vue SPA
@app.get("/{full_path:path}")
async def serve_vue_app(full_path: str):
    """Обслуживает Vue приложение для всех путей (SPA)"""
    # Проверяем, не начинается ли путь с /api/
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")

    if frontend_dist_path.exists():
        index_file = frontend_dist_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )