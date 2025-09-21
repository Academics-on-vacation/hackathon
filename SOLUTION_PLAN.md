# План реализации сервиса анализа полетов БВС

## Анализ задачи и данных

### Основная задача
Создать облачный сервис с REST API для анализа полетов гражданских беспилотных воздушных судов (БВС) в регионах РФ на основе данных Росавиации.

### Анализ структуры данных

#### Файл 2024.xlsx
- **14 листов** по регионам: Москва, Санкт-Петербург, Калининград, Ростов-на-Дону, Самара, Екатеринбург, Тюмень, Новосибирск, Красноярск, Иркутск, Якутск, Магадан, Хабаровск, Симферополь
- **Различные форматы данных** по регионам:
  - Москва: 4 колонки (Дата полёта, SHR, DEP, ARR)
  - Новосибирск: 13 колонок (детальная информация о рейсах)
  - Красноярск, Иркутск, Якутск: 3 колонки (SHR, DEP, ARR)
  - Магадан, Хабаровск: 4 колонки с различными заголовками

#### Файл 2025.xlsx
- **2 листа**: Result_1 (агрегированные данные), Лист1 (пустой)
- **Формат Result_1**: 4 колонки (Центр ЕС ОрВД, SHR, DEP, ARR)

#### Ключевые поля в телеграммах
- **SHR** (Share) - план полета с координатами, временем, типом БВС
- **DEP** (Departure) - сообщение о вылете
- **ARR** (Arrival) - сообщение о посадке
- **Координаты** в формате DDMMN/DDDMME (градусы, минуты, N/S, E/W)
- **Время** в формате HHMM
- **Дата** в формате DOF/YYMMDD
- **Регистрационный номер** БВС
- **Тип БВС** (BLA, BPLA и др.)

## Архитектура решения

### Технологический стек
- **Backend**: Python + FastAPI
- **База данных**: PostgreSQL + PostGIS (для геопространственных данных)
- **Frontend**: React + TypeScript
- **Контейнеризация**: Docker + Docker Compose
- **Мониторинг**: Prometheus + Grafana
- **Документация**: Swagger UI

### Компоненты системы

#### 1. Парсер телеграмм (`telegram_parser/`)
```python
class TelegramParser:
    def parse_shr_message(self, message: str) -> FlightPlan
    def parse_dep_message(self, message: str) -> Departure
    def parse_arr_message(self, message: str) -> Arrival
    def extract_coordinates(self, coord_str: str) -> Tuple[float, float]
    def extract_datetime(self, date_str: str, time_str: str) -> datetime
```

#### 2. Геопривязка (`geo_binding/`)
```python
class GeoBinding:
    def load_regions_shapefile(self, shapefile_path: str)
    def find_region_by_coordinates(self, lat: float, lon: float) -> str
    def update_regions_monthly(self)
```

#### 3. Модели данных (`models/`)
```python
class Flight(BaseModel):
    id: str
    flight_id: str
    aircraft_type: str
    registration: str
    departure_coords: Tuple[float, float]
    arrival_coords: Tuple[float, float]
    departure_time: datetime
    arrival_time: datetime
    duration: timedelta
    region: str
    operator: str
```

#### 4. API сервис (`api/`)
```python
@app.post("/flights/import")
async def import_flights(file: UploadFile)

@app.get("/flights/statistics")
async def get_statistics(region: str = None, date_from: date = None, date_to: date = None)

@app.get("/flights/rating")
async def get_regions_rating(date_from: date, date_to: date)

@app.get("/flights/export")
async def export_report(format: str = "json")
```

#### 5. Аналитика (`analytics/`)
```python
class FlightAnalytics:
    def calculate_basic_metrics(self, flights: List[Flight]) -> BasicMetrics
    def calculate_extended_metrics(self, flights: List[Flight]) -> ExtendedMetrics
    def generate_region_rating(self, period: DateRange) -> List[RegionRating]
    def calculate_flight_density(self, region: str, flights: List[Flight]) -> float
```

## Детальный план реализации

### Этап 1: Анализ требований и архитектуры системы ✅
- [x] Изучение технического задания
- [x] Анализ структуры данных
- [x] Проектирование архитектуры системы
- [x] Выбор технологического стека

### Этап 2: Проектирование базы данных и моделей данных
**Задачи:**
- Создание схемы PostgreSQL с PostGIS
- Проектирование таблиц для полетов, регионов, операторов
- Создание индексов для оптимизации запросов
- Разработка моделей Pydantic для валидации данных

**Структура БД:**
```sql
-- Таблица регионов РФ
CREATE TABLE regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(10) NOT NULL,
    geometry GEOMETRY(MULTIPOLYGON, 4326),
    area_km2 FLOAT
);

-- Таблица полетов
CREATE TABLE flights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flight_id VARCHAR(50),
    aircraft_type VARCHAR(50),
    registration VARCHAR(50),
    departure_coords GEOMETRY(POINT, 4326),
    arrival_coords GEOMETRY(POINT, 4326),
    departure_time TIMESTAMP WITH TIME ZONE,
    arrival_time TIMESTAMP WITH TIME ZONE,
    duration INTERVAL,
    region_id INTEGER REFERENCES regions(id),
    operator VARCHAR(255),
    raw_shr_message TEXT,
    raw_dep_message TEXT,
    raw_arr_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для оптимизации
CREATE INDEX idx_flights_departure_time ON flights(departure_time);
CREATE INDEX idx_flights_region_id ON flights(region_id);
CREATE INDEX idx_flights_departure_coords ON flights USING GIST(departure_coords);
```

### Этап 3: Создание парсера для обработки телеграмм полетов БВС
**Задачи:**
- Парсинг SHR сообщений (планы полетов)
- Парсинг DEP сообщений (вылеты)
- Парсинг ARR сообщений (посадки)
- Извлечение координат из различных форматов
- Обработка дат и времени
- Валидация и нормализация данных

**Примеры парсинга:**
```python
# Координаты: 5509N03737E -> (55.15, 37.617)
# Время: ZZZZ0900 -> 09:00 UTC
# Дата: DOF/240101 -> 2024-01-01
```

### Этап 4: Реализация геопривязки к регионам РФ
**Задачи:**
- Загрузка шейп-файлов границ субъектов РФ
- Создание функций для определения региона по координатам
- Реализация ежемесячного обновления границ
- Оптимизация пространственных запросов

### Этап 5: Разработка REST API для работы с данными
**Основные эндпоинты:**
```
POST /api/v1/flights/import - Импорт данных полетов
GET /api/v1/flights - Получение списка полетов с фильтрацией
GET /api/v1/flights/{id} - Получение детальной информации о полете
GET /api/v1/statistics/basic - Базовые метрики
GET /api/v1/statistics/extended - Расширенные метрики
GET /api/v1/regions/rating - Рейтинг регионов по активности
GET /api/v1/reports/export - Экспорт отчетов (JSON/PNG/JPEG)
```

### Этап 6: Создание системы расчета метрик и аналитики
**Базовые метрики:**
- Общее количество полетов по регионам
- Средняя длительность полетов
- Топ-10 регионов по активности

**Расширенные метрики:**
- Пиковая нагрузка (макс. полетов за час)
- Среднесуточная динамика
- Рост/падение активности по месяцам
- FlightDensity (полетов на 1000 км²)
- Дневная активность (распределение по часам)
- Количество дней без полетов

### Этап 7: Разработка веб-интерфейса для визуализации
**Компоненты интерфейса:**
- Dashboard с основными метриками
- Карта России с тепловой картой полетов
- Графики временных рядов
- Таблицы с детальными данными
- Фильтры по регионам, датам, типам БВС
- Экспорт отчетов

### Этап 8: Настройка системы мониторинга и логирования
**Компоненты:**
- Prometheus для сбора метрик
- Grafana для визуализации мониторинга
- ELK Stack для логирования
- Jaeger для трассировки запросов
- Health checks для всех сервисов

### Этап 9: Создание документации и тестов
**Документация:**
- API документация через Swagger UI
- Техническая документация
- Инструкции по развертыванию
- Руководство пользователя

**Тестирование:**
- Unit тесты (покрытие ≥80%)
- Интеграционные тесты
- Тесты API
- Тесты парсера телеграмм

### Этап 10: Развертывание и настройка CI/CD
**Инфраструктура:**
- Docker контейнеры для всех сервисов
- Docker Compose для локальной разработки
- CI/CD pipeline (GitHub Actions)
- Автоматическое тестирование и деплой

## Критерии приемки

### Функциональные требования
- ✅ Корректный парсинг ≥99% валидных записей
- ✅ Геопривязка строго по границам без ошибок
- ✅ Время обработки 10,000 полетов ≤ 5 мин
- ✅ Доступность API 99.5%
- ✅ Полная документация и тесты

### Технические требования
- ✅ Микросервисная архитектура
- ✅ Автоматическое масштабирование
- ✅ Мониторинг и логирование
- ✅ Безопасность (TLS, аутентификация)
- ✅ Соответствие ГОСТ и ФЗ

## Временные рамки
- **Общее время реализации**: 2-3 недели
- **MVP версия**: 1 неделя
- **Полная версия с документацией**: 2-3 недели

## Риски и митигация
1. **Сложность парсинга разнородных форматов** - создание гибкого парсера с поддержкой различных форматов
2. **Производительность геопривязки** - использование пространственных индексов PostGIS
3. **Масштабируемость** - микросервисная архитектура с возможностью горизонтального масштабирования
4. **Качество данных** - валидация и очистка данных на всех этапах