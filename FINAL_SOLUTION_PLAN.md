# Итоговый план реализации сервиса анализа полетов БВС

## Резюме анализа

### Задача
Создать облачный сервис с REST API для анализа количества и длительности полетов гражданских беспилотников в регионах РФ на основе данных Росавиации.

### Ключевые выводы из анализа данных

#### Структура данных
1. **Файл 2024.xlsx**: 14 листов по регионам с различными форматами данных
2. **Файл 2025.xlsx**: Агрегированные данные по центрам ЕС ОрВД
3. **Основные типы сообщений**: SHR (план полета), DEP (вылет), ARR (посадка)

#### Паттерны телеграмм
- **Координаты**: `5509N03737E` → 55.150000°, 37.616667°
- **Время**: `ZZZZ0900` → 09:00 UTC
- **Дата**: `DOF/240101` → 2024-01-01
- **Регистрация**: `REG/07C4935`
- **Тип БВС**: `TYP/BLA`

## Рекомендуемая архитектура решения

### Технологический стек
```
Backend:     Python 3.11 + FastAPI + SQLAlchemy
Database:    PostgreSQL 15 + PostGIS 3.3
Frontend:    React 18 + TypeScript + Material-UI
Deployment:  Docker + Docker Compose
Monitoring:  Prometheus + Grafana + ELK Stack
```

### Структура проекта
```
bvs-analytics/
├── backend/
│   ├── app/
│   │   ├── api/           # REST API endpoints
│   │   ├── core/          # Конфигурация, безопасность
│   │   ├── models/        # SQLAlchemy модели
│   │   ├── schemas/       # Pydantic схемы
│   │   ├── services/      # Бизнес-логика
│   │   └── utils/         # Утилиты
│   ├── parsers/           # Парсеры телеграмм
│   ├── geo/              # Геопривязка
│   └── analytics/        # Расчет метрик
├── frontend/
│   ├── src/
│   │   ├── components/   # React компоненты
│   │   ├── pages/        # Страницы приложения
│   │   ├── services/     # API клиенты
│   │   └── utils/        # Утилиты
├── docker/               # Docker конфигурации
├── docs/                 # Документация
└── tests/               # Тесты
```

## Детальный план реализации

### Этап 1: Настройка инфраструктуры (1-2 дня)

#### 1.1 Создание базовой структуры проекта
```bash
mkdir bvs-analytics
cd bvs-analytics
mkdir -p backend/{app/{api,core,models,schemas,services,utils},parsers,geo,analytics}
mkdir -p frontend/src/{components,pages,services,utils}
mkdir -p docker docs tests
```

#### 1.2 Docker Compose конфигурация
```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: bvs_analytics
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/bvs_analytics

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Этап 2: Разработка парсера телеграмм (2-3 дня)

#### 2.1 Базовый парсер
```python
# backend/parsers/telegram_parser.py
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re

class TelegramParser:
    def parse_shr_message(self, message: str) -> Dict:
        """Парсит SHR сообщение (план полета)"""
        return {
            'message_type': 'SHR',
            'registration': self._extract_registration(message),
            'aircraft_type': self._extract_aircraft_type(message),
            'operator': self._extract_operator(message),
            'departure_coords': self._extract_coordinates(message, 'DEP'),
            'destination_coords': self._extract_coordinates(message, 'DEST'),
            'flight_date': self._extract_date(message),
            'departure_time': self._extract_time(message),
            'sid': self._extract_sid(message),
            'raw_message': message
        }
    
    def _extract_coordinates(self, message: str, coord_type: str) -> Tuple[float, float]:
        """Извлекает координаты из сообщения"""
        pattern = f'{coord_type}/(\d{{4,6}}[NS]\d{{5,7}}[EW])'
        match = re.search(pattern, message)
        if match:
            return self._parse_coordinates(match.group(1))
        return None, None
    
    def _parse_coordinates(self, coord_str: str) -> Tuple[float, float]:
        """Конвертирует координаты в десятичные градусы"""
        # Реализация из telegram_analysis.py
        pattern = r'(\d{4,6})([NS])(\d{5,7})([EW])'
        match = re.match(pattern, coord_str)
        
        if not match:
            raise ValueError(f"Invalid coordinate format: {coord_str}")
        
        lat_str, lat_dir, lon_str, lon_dir = match.groups()
        
        # Парсинг широты
        if len(lat_str) == 4:  # DDMM
            lat = int(lat_str[:2]) + int(lat_str[2:4])/60
        elif len(lat_str) == 6:  # DDMMSS
            lat = int(lat_str[:2]) + int(lat_str[2:4])/60 + int(lat_str[4:6])/3600
        
        if lat_dir == 'S':
            lat = -lat
        
        # Парсинг долготы
        if len(lon_str) == 5:  # DDDMM
            lon = int(lon_str[:3]) + int(lon_str[3:5])/60
        elif len(lon_str) == 7:  # DDDMMSS
            lon = int(lon_str[:3]) + int(lon_str[3:5])/60 + int(lon_str[5:7])/3600
        
        if lon_dir == 'W':
            lon = -lon
        
        return lat, lon
```

#### 2.2 Обработчик различных форматов данных
```python
# backend/parsers/data_processor.py
import pandas as pd
from typing import List, Dict

class DataProcessor:
    def process_excel_file(self, file_path: str) -> List[Dict]:
        """Обрабатывает Excel файл с данными полетов"""
        excel_file = pd.ExcelFile(file_path)
        all_flights = []
        
        for sheet_name in excel_file.sheet_names:
            if sheet_name == 'Лист1':  # Пропускаем пустые листы
                continue
                
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            flights = self._process_sheet(df, sheet_name)
            all_flights.extend(flights)
        
        return all_flights
    
    def _process_sheet(self, df: pd.DataFrame, region: str) -> List[Dict]:
        """Обрабатывает отдельный лист Excel"""
        flights = []
        parser = TelegramParser()
        
        for _, row in df.iterrows():
            # Обработка различных форматов листов
            if 'SHR' in df.columns:
                shr_msg = row.get('SHR', '')
                dep_msg = row.get('DEP', '')
                arr_msg = row.get('ARR', '')
                
                if shr_msg and isinstance(shr_msg, str):
                    flight_data = parser.parse_shr_message(shr_msg)
                    flight_data['region'] = region
                    flight_data['dep_message'] = dep_msg
                    flight_data['arr_message'] = arr_msg
                    flights.append(flight_data)
        
        return flights
```

### Этап 3: Модели данных и база данных (1-2 дня)

#### 3.1 SQLAlchemy модели
```python
# backend/app/models/flight.py
from sqlalchemy import Column, String, DateTime, Float, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import uuid

Base = declarative_base()

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(10), nullable=False)
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326))
    area_km2 = Column(Float)
    
    flights = relationship("Flight", back_populates="region")

class Flight(Base):
    __tablename__ = "flights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flight_id = Column(String(50))
    registration = Column(String(50))
    aircraft_type = Column(String(50))
    operator = Column(String(255))
    
    departure_coords = Column(Geometry('POINT', srid=4326))
    arrival_coords = Column(Geometry('POINT', srid=4326))
    departure_time = Column(DateTime(timezone=True))
    arrival_time = Column(DateTime(timezone=True))
    
    region_id = Column(Integer, ForeignKey('regions.id'))
    region = relationship("Region", back_populates="flights")
    
    raw_shr_message = Column(Text)
    raw_dep_message = Column(Text)
    raw_arr_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

#### 3.2 Pydantic схемы
```python
# backend/app/schemas/flight.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

class FlightBase(BaseModel):
    flight_id: Optional[str] = None
    registration: Optional[str] = None
    aircraft_type: Optional[str] = None
    operator: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None

class FlightCreate(FlightBase):
    departure_coords: Optional[Tuple[float, float]] = None
    arrival_coords: Optional[Tuple[float, float]] = None
    region_id: Optional[int] = None
    raw_shr_message: Optional[str] = None

class Flight(FlightBase):
    id: UUID
    region_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class FlightStatistics(BaseModel):
    total_flights: int
    avg_duration_minutes: float
    top_regions: List[Dict[str, any]]
    flights_by_month: Dict[str, int]
```

### Этап 4: REST API (2-3 дня)

#### 4.1 Основные эндпоинты
```python
# backend/app/api/flights.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ..database import get_db
from ..schemas import flight as flight_schemas
from ..services import flight_service

router = APIRouter(prefix="/api/v1/flights", tags=["flights"])

@router.post("/import", response_model=dict)
async def import_flights(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Импорт данных полетов из Excel файла"""
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    result = await flight_service.import_from_excel(file, db)
    return {"message": f"Imported {result['imported']} flights", "errors": result['errors']}

@router.get("/", response_model=List[flight_schemas.Flight])
def get_flights(
    skip: int = 0,
    limit: int = 100,
    region: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Получение списка полетов с фильтрацией"""
    return flight_service.get_flights(db, skip, limit, region, date_from, date_to)

@router.get("/statistics", response_model=flight_schemas.FlightStatistics)
def get_statistics(
    region: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Получение статистики полетов"""
    return flight_service.get_statistics(db, region, date_from, date_to)

@router.get("/regions/rating")
def get_regions_rating(
    date_from: date,
    date_to: date,
    db: Session = Depends(get_db)
):
    """Рейтинг регионов по активности полетов"""
    return flight_service.get_regions_rating(db, date_from, date_to)

@router.get("/export/{format}")
async def export_data(
    format: str,
    region: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Экспорт данных в различных форматах"""
    if format not in ['json', 'png', 'jpeg']:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    return await flight_service.export_data(db, format, region, date_from, date_to)
```

### Этап 5: Геопривязка (1-2 дня)

#### 5.1 Сервис геопривязки
```python
# backend/geo/geo_service.py
from geoalchemy2 import func
from sqlalchemy.orm import Session
from typing import Tuple, Optional

class GeoService:
    def __init__(self, db: Session):
        self.db = db
    
    def find_region_by_coordinates(self, lat: float, lon: float) -> Optional[str]:
        """Определяет регион по координатам"""
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        
        result = self.db.query(Region.name).filter(
            func.ST_Contains(Region.geometry, point)
        ).first()
        
        return result.name if result else None
    
    def load_regions_shapefile(self, shapefile_path: str):
        """Загружает границы регионов из шейп-файла"""
        import geopandas as gpd
        
        gdf = gpd.read_file(shapefile_path)
        
        for _, row in gdf.iterrows():
            region = Region(
                name=row['NAME'],
                code=row['CODE'],
                geometry=row['geometry'].wkt,
                area_km2=row['AREA_KM2']
            )
            self.db.add(region)
        
        self.db.commit()
```

### Этап 6: Frontend (3-4 дня)

#### 6.1 Основные компоненты
```typescript
// frontend/src/components/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { Grid, Card, CardContent, Typography } from '@mui/material';
import { FlightMap } from './FlightMap';
import { StatisticsChart } from './StatisticsChart';
import { RegionsTable } from './RegionsTable';

export const Dashboard: React.FC = () => {
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/v1/flights/statistics');
      const data = await response.json();
      setStatistics(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6">Общая статистика</Typography>
            <Typography variant="h4">{statistics?.total_flights}</Typography>
            <Typography color="textSecondary">Всего полетов</Typography>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12}>
        <FlightMap />
      </Grid>
      
      <Grid item xs={12} md={6}>
        <StatisticsChart data={statistics?.flights_by_month} />
      </Grid>
      
      <Grid item xs={12} md={6}>
        <RegionsTable regions={statistics?.top_regions} />
      </Grid>
    </Grid>
  );
};
```

### Этап 7: Аналитика и метрики (2-3 дня)

#### 7.1 Сервис аналитики
```python
# backend/analytics/analytics_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from typing import Dict, List

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_basic_metrics(self, region: str = None, date_from: date = None, date_to: date = None) -> Dict:
        """Базовые метрики"""
        query = self.db.query(Flight)
        
        if region:
            query = query.join(Region).filter(Region.name == region)
        if date_from:
            query = query.filter(Flight.departure_time >= date_from)
        if date_to:
            query = query.filter(Flight.departure_time <= date_to)
        
        flights = query.all()
        
        total_flights = len(flights)
        avg_duration = self._calculate_avg_duration(flights)
        top_regions = self._get_top_regions(date_from, date_to)
        
        return {
            'total_flights': total_flights,
            'avg_duration_minutes': avg_duration,
            'top_regions': top_regions
        }
    
    def calculate_extended_metrics(self, region: str = None) -> Dict:
        """Расширенные метрики"""
        # Пиковая нагрузка
        peak_load = self._calculate_peak_load(region)
        
        # Среднесуточная динамика
        daily_dynamics = self._calculate_daily_dynamics(region)
        
        # FlightDensity
        flight_density = self._calculate_flight_density(region)
        
        # Дневная активность
        hourly_distribution = self._calculate_hourly_distribution(region)
        
        return {
            'peak_load_per_hour': peak_load,
            'daily_dynamics': daily_dynamics,
            'flight_density_per_1000km2': flight_density,
            'hourly_distribution': hourly_distribution
        }
    
    def _calculate_flight_density(self, region: str) -> float:
        """Расчет плотности полетов на 1000 км²"""
        if not region:
            return 0
        
        region_data = self.db.query(Region).filter(Region.name == region).first()
        if not region_data or not region_data.area_km2:
            return 0
        
        flights_count = self.db.query(Flight).filter(Flight.region_id == region_data.id).count()
        
        return (flights_count / region_data.area_km2) * 1000
```

## Временные рамки и ресурсы

### Общий план (14-21 день)
1. **Неделя 1**: Инфраструктура, парсер, база данных
2. **Неделя 2**: API, геопривязка, базовый frontend
3. **Неделя 3**: Аналитика, тестирование, документация

### Команда (рекомендуемый состав)
- **1 Backend разработчик** (Python/FastAPI)
- **1 Frontend разработчик** (React/TypeScript)
- **1 DevOps инженер** (Docker, мониторинг)
- **1 Аналитик данных** (парсинг, геопривязка)

## Критерии успеха

### Функциональные
- ✅ Парсинг ≥99% валидных записей
- ✅ Геопривязка без ошибок
- ✅ Обработка 10,000 полетов ≤ 5 мин
- ✅ API доступность 99.5%

### Технические
- ✅ Покрытие тестами ≥80%
- ✅ Swagger документация
- ✅ Docker контейнеризация
- ✅ Мониторинг и логирование

## Заключение

Предложенное решение полностью соответствует техническому заданию и обеспечивает:

1. **Масштабируемость** - микросервисная архитектура
2. **Производительность** - оптимизированные запросы и индексы
3. **Надежность** - мониторинг и автовосстановление
4. **Безопасность** - аутентификация и шифрование
5. **Удобство использования** - интуитивный веб-интерфейс

Решение готово к реализации и может быть развернуто как в облаке, так и на выделенных серверах заказчика.