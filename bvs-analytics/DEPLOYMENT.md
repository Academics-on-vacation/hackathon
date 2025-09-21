# Развертывание BVS Analytics на сервере

## Подготовка к развертыванию

### 1. Подключение к серверу
```bash
ssh server
```

### 2. Установка зависимостей на сервере
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.11+
sudo apt install python3 python3-pip python3-venv -y

# Установка дополнительных пакетов
sudo apt install git curl wget -y
```

### 3. Копирование проекта на сервер

#### Вариант A: Через SCP (с локальной машины)
```bash
# Из директории hackathon на локальной машине
scp -r bvs-analytics server:~/
```

#### Вариант B: Через Git (если проект в репозитории)
```bash
# На сервере
git clone <repository-url>
cd bvs-analytics
```

#### Вариант C: Создание архива
```bash
# На локальной машине
cd /Users/mrralexandrov/projects/hackathon
tar -czf bvs-analytics.tar.gz bvs-analytics/
scp bvs-analytics.tar.gz server:~/

# На сервере
tar -xzf bvs-analytics.tar.gz
cd bvs-analytics
```

## Установка и настройка

### 1. Создание виртуального окружения
```bash
cd ~/bvs-analytics/backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install pydantic-settings
```

### 3. Настройка конфигурации
```bash
# Создание .env файла
cp .env.example .env

# Редактирование конфигурации
nano .env
```

Настройте следующие параметры в `.env`:
```env
# Database (для продакшена можно использовать PostgreSQL)
DATABASE_URL=sqlite:///./bvs_analytics.db

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=BVS Analytics
VERSION=1.0.0

# Security
SECRET_KEY=your-production-secret-key-here

# CORS (добавьте IP сервера)
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://YOUR_SERVER_IP:8000"]

# Logging
LOG_LEVEL=INFO

# File Upload
MAX_UPLOAD_SIZE=50000000
UPLOAD_DIR=./uploads
```

### 4. Тестирование установки
```bash
# Тест парсера
python3 test_parser.py

# Тест API
python3 test_api.py
```

## Запуск сервиса

### 1. Запуск в режиме разработки
```bash
python3 run.py
```

### 2. Запуск в продакшене с Gunicorn
```bash
# Установка Gunicorn
pip install gunicorn

# Запуск сервера
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Запуск как системный сервис

Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/bvs-analytics.service
```

Содержимое файла:
```ini
[Unit]
Description=BVS Analytics API
After=network.target

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/bvs-analytics/backend
Environment=PATH=/home/ubuntu/bvs-analytics/backend/venv/bin
ExecStart=/home/ubuntu/bvs-analytics/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bvs-analytics
sudo systemctl start bvs-analytics
sudo systemctl status bvs-analytics
```

## Настройка веб-сервера (Nginx)

### 1. Установка Nginx
```bash
sudo apt install nginx -y
```

### 2. Настройка конфигурации
```bash
sudo nano /etc/nginx/sites-available/bvs-analytics
```

Содержимое конфигурации:
```nginx
server {
    listen 80;
    server_name YOUR_SERVER_IP;

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Документация API
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Статические файлы фронтенда
    location / {
        root /home/ubuntu/bvs-analytics/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Логи
    access_log /var/log/nginx/bvs-analytics.access.log;
    error_log /var/log/nginx/bvs-analytics.error.log;
}
```

### 3. Активация конфигурации
```bash
sudo ln -s /etc/nginx/sites-available/bvs-analytics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Проверка развертывания

### 1. Проверка API
```bash
# Health check
curl http://YOUR_SERVER_IP/health

# Базовые метрики
curl http://YOUR_SERVER_IP/api/v1/flights/statistics/basic

# Рейтинг регионов
curl http://YOUR_SERVER_IP/api/v1/flights/regions/rating
```

### 2. Проверка веб-интерфейса
Откройте в браузере: `http://YOUR_SERVER_IP`

### 3. Проверка документации API
- Swagger UI: `http://YOUR_SERVER_IP/docs`
- ReDoc: `http://YOUR_SERVER_IP/redoc`

## Импорт данных

### 1. Через веб-интерфейс
1. Откройте `http://YOUR_SERVER_IP`
2. Перетащите Excel файл в область загрузки
3. Нажмите "Загрузить файл"

### 2. Через API
```bash
curl -X POST "http://YOUR_SERVER_IP/api/v1/flights/import" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/data/2024.xlsx"
```

### 3. Копирование данных на сервер
```bash
# С локальной машины
scp data/*.xlsx server:~/bvs-analytics/backend/uploads/
```

## Мониторинг и логи

### 1. Просмотр логов сервиса
```bash
sudo journalctl -u bvs-analytics -f
```

### 2. Просмотр логов приложения
```bash
tail -f ~/bvs-analytics/backend/bvs_analytics.log
```

### 3. Просмотр логов Nginx
```bash
sudo tail -f /var/log/nginx/bvs-analytics.access.log
sudo tail -f /var/log/nginx/bvs-analytics.error.log
```

### 4. Мониторинг ресурсов
```bash
# Использование CPU и памяти
htop

# Дисковое пространство
df -h

# Сетевые подключения
netstat -tulpn | grep :8000
```

## Обновление приложения

### 1. Остановка сервиса
```bash
sudo systemctl stop bvs-analytics
```

### 2. Обновление кода
```bash
cd ~/bvs-analytics
# Копирование новых файлов или git pull
```

### 3. Обновление зависимостей
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Запуск сервиса
```bash
sudo systemctl start bvs-analytics
```

## Резервное копирование

### 1. Создание бэкапа базы данных
```bash
cp ~/bvs-analytics/backend/bvs_analytics.db ~/backups/bvs_analytics_$(date +%Y%m%d_%H%M%S).db
```

### 2. Создание полного бэкапа
```bash
tar -czf ~/backups/bvs-analytics_backup_$(date +%Y%m%d_%H%M%S).tar.gz ~/bvs-analytics/
```

## Устранение неполадок

### 1. Сервис не запускается
```bash
# Проверка статуса
sudo systemctl status bvs-analytics

# Проверка логов
sudo journalctl -u bvs-analytics --no-pager

# Проверка портов
sudo netstat -tulpn | grep :8000
```

### 2. Ошибки импорта данных
```bash
# Проверка прав доступа
ls -la ~/bvs-analytics/backend/uploads/

# Проверка размера файлов
du -h ~/bvs-analytics/backend/uploads/*

# Проверка логов приложения
tail -f ~/bvs-analytics/backend/bvs_analytics.log
```

### 3. Проблемы с производительностью
```bash
# Увеличение количества воркеров Gunicorn
sudo nano /etc/systemd/system/bvs-analytics.service
# Измените -w 4 на -w 8

sudo systemctl daemon-reload
sudo systemctl restart bvs-analytics
```

## Безопасность

### 1. Настройка файрвола
```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS (если используется SSL)
sudo ufw enable
```

### 2. SSL сертификат (опционально)
```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение сертификата
sudo certbot --nginx -d your-domain.com
```

### 3. Ограничение доступа к API
Добавьте в конфигурацию Nginx:
```nginx
# Ограничение по IP
location /api/v1/flights/import {
    allow YOUR_ADMIN_IP;
    deny all;
    proxy_pass http://127.0.0.1:8000;
}
```

## Контакты и поддержка

При возникновении проблем:
1. Проверьте логи сервиса и приложения
2. Убедитесь, что все зависимости установлены
3. Проверьте конфигурацию .env файла
4. Убедитесь, что порты не заблокированы файрволом

Для получения помощи создайте Issue в репозитории проекта с описанием проблемы и логами.