#!/usr/bin/env python3
"""
Скрипт для запуска BVS Analytics API
"""

import sys
import os
import uvicorn
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    # Создаем .env файл если его нет
    env_file = root_dir / ".env"
    if not env_file.exists():
        print("Creating .env file...")
        with open(env_file, "w") as f:
            f.write("""# Database
DATABASE_URL=sqlite:///./bvs_analytics.db

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=BVS Analytics
VERSION=1.0.0
DESCRIPTION=Сервис анализа полетов БВС

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]

# Logging
LOG_LEVEL=INFO

# File Upload
MAX_UPLOAD_SIZE=50000000
UPLOAD_DIR=./uploads
""")
    
    # Создаем директорию для загрузок
    upload_dir = root_dir / "uploads"
    upload_dir.mkdir(exist_ok=True)
    
    print("Starting BVS Analytics API...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    print("Press Ctrl+C to stop")
    
    # Запускаем сервер
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8800,
        reload=True,
        log_level="info"
    )