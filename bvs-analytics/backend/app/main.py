import os
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
        # Логируем содержимое для отладки
        for item in frontend_dist_path.rglob("*"):
            if item.is_file():
                logger.debug(f"Frontend file: {item.relative_to(frontend_dist_path)}")
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

# ВСЕ API РОУТЕРЫ ДОЛЖНЫ БЫТЬ ЗДЕСЬ - ПЕРВЫМИ!
app.include_router(
    flights_router,
    prefix=f"{settings.API_V1_STR}",
    tags=["flights"]
)

app.include_router(
    auth_router,
    tags=["auth"]
)

# 3. Фронтенд с префиксом /app
@app.get("/{full_path:path}")
async def serve_vue_app(full_path: str):
    """Обслуживает Vue приложение для всех путей (SPA)"""
    # ИСКЛЮЧАЕМ ВСЕ API ПУТИ
    excluded_paths = [
        "api/", "docs", "redoc", "health", "openapi.json",
        f"{settings.API_V1_STR}/", "auth/"
    ]

    if any(full_path.startswith(path) for path in excluded_paths):
        raise HTTPException(status_code=404, detail="Route not found")

    # Проверяем статические файлы
    if full_path.endswith(('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp')):
        static_file = frontend_dist_path / full_path
        if static_file.exists():
            return FileResponse(static_file)

    # Все остальные пути ведут на index.html
    if frontend_dist_path.exists():
        index_file = frontend_dist_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend not found")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )