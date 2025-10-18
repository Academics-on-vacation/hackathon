from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "BVS Analytics"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Сервис анализа полетов БВС"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/bvs_analytics"
    # DATABASE_URL: str = "sqlite:///./bvs_analytics.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 50000000  # 50MB
    UPLOAD_DIR: str = "./uploads"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # LaTeX Reports
    LATEX_COMPILER: str = "pdflatex"
    COMPILE_RETRY: int = 3
    SAVE_DIR: str = "reports"
    IMAGE_DIR: str = "images"
    REPORT_DIR: str = "./reports"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Создаем директорию для загрузок если её нет
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

settings = Settings()