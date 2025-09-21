from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime

from ..core.database import get_db
from ..schemas.flight import (
    Flight, FlightCreate, FlightFilter, FlightImportResult,
    FlightStatistics, BasicMetrics, ExtendedMetrics, RegionRating
)
from ..services.flight_service import FlightService

router = APIRouter(prefix="/flights", tags=["flights"])

@router.post("/import", response_model=FlightImportResult)
async def import_flights(
    file: UploadFile = File(..., description="Excel файл с данными полетов"),
    db: Session = Depends(get_db)
):
    """
    Импорт данных полетов из Excel файла
    
    Поддерживаемые форматы:
    - Файлы с листами по регионам (формат 2024.xlsx)
    - Агрегированные данные (формат 2025.xlsx)
    """
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400, 
            detail="Поддерживаются только Excel файлы (.xlsx)"
        )
    
    service = FlightService(db)
    result = await service.import_from_excel(file)
    
    return FlightImportResult(
        imported=result['imported'],
        errors=result['errors'],
        total_processed=result['total_processed']
    )

@router.get("/", response_model=List[Flight])
def get_flights(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    region: Optional[str] = Query(None, description="Фильтр по региону"),
    aircraft_type: Optional[str] = Query(None, description="Фильтр по типу БВС"),
    operator: Optional[str] = Query(None, description="Фильтр по оператору"),
    registration: Optional[str] = Query(None, description="Фильтр по регистрационному номеру"),
    date_from: Optional[date] = Query(None, description="Дата начала периода"),
    date_to: Optional[date] = Query(None, description="Дата окончания периода"),
    db: Session = Depends(get_db)
):
    """
    Получение списка полетов с фильтрацией
    
    Поддерживаемые фильтры:
    - По региону
    - По типу БВС
    - По оператору
    - По регистрационному номеру
    - По диапазону дат
    """
    filters = FlightFilter(
        region=region,
        aircraft_type=aircraft_type,
        operator=operator,
        registration=registration,
        date_from=datetime.combine(date_from, datetime.min.time()) if date_from else None,
        date_to=datetime.combine(date_to, datetime.max.time()) if date_to else None
    )
    
    service = FlightService(db)
    return service.get_flights(skip=skip, limit=limit, filters=filters)

@router.get("/{flight_id}", response_model=Flight)
def get_flight(
    flight_id: str,
    db: Session = Depends(get_db)
):
    """Получение детальной информации о полете"""
    service = FlightService(db)
    flight = service.get_flight_by_id(flight_id)
    
    if not flight:
        raise HTTPException(status_code=404, detail="Полет не найден")
    
    return flight

@router.get("/statistics/basic", response_model=BasicMetrics)
def get_basic_statistics(
    region: Optional[str] = Query(None, description="Фильтр по региону"),
    aircraft_type: Optional[str] = Query(None, description="Фильтр по типу БВС"),
    operator: Optional[str] = Query(None, description="Фильтр по оператору"),
    date_from: Optional[date] = Query(None, description="Дата начала периода"),
    date_to: Optional[date] = Query(None, description="Дата окончания периода"),
    db: Session = Depends(get_db)
):
    """
    Получение базовых метрик полетов
    
    Включает:
    - Общее количество полетов
    - Среднюю длительность полетов
    - Количество уникальных БВС
    - Количество уникальных операторов
    - Диапазон дат
    """
    filters = FlightFilter(
        region=region,
        aircraft_type=aircraft_type,
        operator=operator,
        date_from=datetime.combine(date_from, datetime.min.time()) if date_from else None,
        date_to=datetime.combine(date_to, datetime.max.time()) if date_to else None
    )
    
    service = FlightService(db)
    return service.get_basic_metrics(filters)

@router.get("/statistics/extended", response_model=ExtendedMetrics)
def get_extended_statistics(
    region: Optional[str] = Query(None, description="Фильтр по региону"),
    aircraft_type: Optional[str] = Query(None, description="Фильтр по типу БВС"),
    date_from: Optional[date] = Query(None, description="Дата начала периода"),
    date_to: Optional[date] = Query(None, description="Дата окончания периода"),
    db: Session = Depends(get_db)
):
    """
    Получение расширенных метрик полетов
    
    Включает:
    - Пиковую нагрузку по часам
    - Плотность полетов на 1000 км²
    - Распределение полетов по часам
    - Распределение полетов по дням недели
    - Количество дней без полетов
    """
    filters = FlightFilter(
        region=region,
        aircraft_type=aircraft_type,
        date_from=datetime.combine(date_from, datetime.min.time()) if date_from else None,
        date_to=datetime.combine(date_to, datetime.max.time()) if date_to else None
    )
    
    service = FlightService(db)
    return service.get_extended_metrics(filters)

@router.get("/statistics/summary")
def get_statistics_summary(
    region: Optional[str] = Query(None, description="Фильтр по региону"),
    aircraft_type: Optional[str] = Query(None, description="Фильтр по типу БВС"),
    date_from: Optional[date] = Query(None, description="Дата начала периода"),
    date_to: Optional[date] = Query(None, description="Дата окончания периода"),
    db: Session = Depends(get_db)
):
    """
    Получение сводной статистики полетов
    
    Объединяет базовые и расширенные метрики, топ регионов,
    распределение по месяцам и типам БВС
    """
    filters = FlightFilter(
        region=region,
        aircraft_type=aircraft_type,
        date_from=datetime.combine(date_from, datetime.min.time()) if date_from else None,
        date_to=datetime.combine(date_to, datetime.max.time()) if date_to else None
    )
    
    service = FlightService(db)
    return service.get_flight_statistics_summary(filters)

@router.get("/regions/rating", response_model=List[RegionRating])
def get_regions_rating(
    date_from: Optional[date] = Query(None, description="Дата начала периода"),
    date_to: Optional[date] = Query(None, description="Дата окончания периода"),
    limit: int = Query(20, ge=1, le=100, description="Количество регионов в рейтинге"),
    db: Session = Depends(get_db)
):
    """
    Рейтинг регионов по активности полетов БВС
    
    Сортировка по количеству полетов (убывание)
    Включает плотность полетов на 1000 км²
    """
    service = FlightService(db)
    ratings = service.get_regions_rating(date_from, date_to)
    return ratings[:limit]

@router.get("/analytics/monthly")
def get_monthly_analytics(
    region: Optional[str] = Query(None, description="Фильтр по региону"),
    db: Session = Depends(get_db)
):
    """Аналитика полетов по месяцам"""
    filters = FlightFilter(region=region) if region else None
    service = FlightService(db)
    return service.get_flights_by_month(filters)

@router.get("/analytics/aircraft-types")
def get_aircraft_types_analytics(
    region: Optional[str] = Query(None, description="Фильтр по региону"),
    db: Session = Depends(get_db)
):
    """Аналитика полетов по типам БВС"""
    filters = FlightFilter(region=region) if region else None
    service = FlightService(db)
    return service.get_flights_by_aircraft_type(filters)

@router.get("/export/{format}")
async def export_flights(
    format: str,
    region: Optional[str] = Query(None, description="Фильтр по региону"),
    aircraft_type: Optional[str] = Query(None, description="Фильтр по типу БВС"),
    date_from: Optional[date] = Query(None, description="Дата начала периода"),
    date_to: Optional[date] = Query(None, description="Дата окончания периода"),
    include_raw: bool = Query(False, description="Включить исходные сообщения"),
    db: Session = Depends(get_db)
):
    """
    Экспорт данных полетов в различных форматах
    
    Поддерживаемые форматы:
    - json: JSON файл с данными
    - csv: CSV файл для Excel
    - xlsx: Excel файл
    - png: График статистики
    - jpeg: График статистики
    """
    if format not in ['json', 'csv', 'xlsx', 'png', 'jpeg']:
        raise HTTPException(
            status_code=400, 
            detail="Поддерживаемые форматы: json, csv, xlsx, png, jpeg"
        )
    
    # TODO: Реализовать экспорт данных
    raise HTTPException(
        status_code=501, 
        detail="Экспорт данных будет реализован в следующей версии"
    )

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Проверка состояния сервиса"""
    try:
        # Проверяем подключение к БД
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")