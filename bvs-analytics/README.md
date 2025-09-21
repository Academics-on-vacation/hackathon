# BVS Analytics - Сервис анализа полетов БВС

Сервис для анализа количества и длительности полетов гражданских беспилотников в регионах Российской Федерации на основе данных Росавиации.

## Возможности

- 📊 **Импорт данных** из Excel файлов различных форматов
- 🔍 **Парсинг телеграмм** полетов БВС (SHR/DEP/ARR сообщения)
- 🗺️ **Геопривязка** полетов к регионам РФ
- 📈 **Аналитика и метрики** полетов
- 🌐 **REST API** для интеграции
- 📋 **Swagger документация** API
- 🎯 **Рейтинг регионов** по активности полетов

## Технологический стек

- **Backend**: Python 3.11+ + FastAPI
- **База данных**: SQLite (для разработки) / PostgreSQL (для продакшена)
- **Парсинг данных**: pandas + openpyxl
- **API документация**: Swagger UI
- **Логирование**: structlog

## Быстрый старт

### 1. Установка зависимостей

```bash
cd bvs-analytics/backend
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
python run.py
```

Сервер будет доступен по адресу: http://localhost:8000

### 3. Документация API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Тестирование

### Тест парсера телеграмм

```bash
cd bvs-analytics/backend
python test_parser.py
```

### Тест API

```bash
# Проверка состояния сервиса
curl http://localhost:8000/health

# Получение базовых метрик
curl http://localhost:8000/api/v1/flights/statistics/basic

# Рейтинг регионов
curl http://localhost:8000/api/v1/flights/regions/rating
```

## Использование API

### Импорт данных

```bash
curl -X POST "http://localhost:8000/api/v1/flights/import" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@data/2024.xlsx"
```

### Получение статистики

```bash
# Базовые метрики
curl "http://localhost:8000/api/v1/flights/statistics/basic"

# Расширенные метрики
curl "http://localhost:8000/api/v1/flights/statistics/extended"

# Сводная статистика
curl "http://localhost:8000/api/v1/flights/statistics/summary"
```

### Фильтрация данных

```bash
# Полеты по региону
curl "http://localhost:8000/api/v1/flights/?region=Москва&limit=10"

# Полеты по типу БВС
curl "http://localhost:8000/api/v1/flights/?aircraft_type=BLA&limit=10"

# Полеты за период
curl "http://localhost:8000/api/v1/flights/?date_from=2024-01-01&date_to=2024-12-31"
```

## Структура проекта

```
bvs-analytics/
├── backend/
│   ├── app/
│   │   ├── api/           # REST API endpoints
│   │   ├── core/          # Конфигурация, БД
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── schemas/       # Pydantic схемы
│   │   └── services/      # Бизнес-логика
│   ├── parsers/           # Парсеры телеграмм
│   ├── requirements.txt   # Зависимости Python
│   ├── run.py            # Скрипт запуска
│   └── test_parser.py    # Тесты парсера
├── docs/                 # Документация
└── README.md
```

## Форматы данных

Сервис поддерживает импорт Excel файлов следующих форматов:

### 1. Формат по регионам (2024.xlsx)
- Листы по регионам: Москва, Санкт-Петербург, и т.д.
- Колонки: SHR, DEP, ARR (телеграммы полетов)

### 2. Детальный формат (Новосибирск)
- Колонки: Рейс, Тип ВС, Борт. номер, Владелец, Время вылета/посадки

### 3. Агрегированный формат (2025.xlsx)
- Колонки: Центр ЕС ОрВД, SHR, DEP, ARR

## Примеры телеграмм

### SHR сообщение (план полета)
```
(SHR-ZZZZZ
-ZZZZ0900
-M0016/M0026 /ZONA R0,7 5509N03737E/
-ZZZZ0900
-DEP/5509N03737E DEST/5509N03737E DOF/240101 EET/UUWV0001
OPR/МЕНЖУЛИН АЛЕКСЕЙ ПЕТРОВИ4 REG/07C4935 TYP/BLA RMK/MР11608
SID/7771445428)
```

### DEP сообщение (вылет)
```
(DEP-ZZZZZ-ZZZZ0900-ZZZZ
-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E DEST/5509N03737E)
```

### ARR сообщение (посадка)
```
(ARR-ZZZZZ-ZZZZ0900-ZZZZ1515
-REG/07C4935 DOF/240101 RMK/MR11608 DEP/5509N03737E DEST/5509N03737E)
```

## Метрики и аналитика

### Базовые метрики
- Общее количество полетов
- Средняя длительность полетов
- Количество уникальных БВС
- Количество уникальных операторов

### Расширенные метрики
- Пиковая нагрузка по часам
- Плотность полетов на 1000 км²
- Распределение полетов по часам
- Распределение по дням недели
- Количество дней без полетов

### Рейтинг регионов
- Сортировка по количеству полетов
- Средняя длительность полетов
- Плотность полетов на площадь региона

## Конфигурация

Основные настройки в файле `.env`:

```env
# База данных
DATABASE_URL=sqlite:///./bvs_analytics.db

# API
API_V1_STR=/api/v1
PROJECT_NAME=BVS Analytics

# Безопасность
SECRET_KEY=your-secret-key

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Загрузка файлов
MAX_UPLOAD_SIZE=50000000
UPLOAD_DIR=./uploads

# Логирование
LOG_LEVEL=INFO
```

## Развертывание

### Локальное развертывание

```bash
# Клонирование и установка
git clone <repository>
cd bvs-analytics/backend
pip install -r requirements.txt

# Запуск
python run.py
```

### Развертывание на сервере

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Запуск с Gunicorn
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Мониторинг

- **Health Check**: `/health`
- **Метрики**: Встроенные метрики FastAPI
- **Логи**: Структурированное логирование в файл и консоль

## Лицензия

Проект разработан для хакатона в соответствии с техническим заданием.

## Поддержка

Для вопросов и предложений создавайте Issues в репозитории проекта.