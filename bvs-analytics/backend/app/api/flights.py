from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ..core.database import get_db
from ..schemas.flight import (
    Flight, FlightCreate, FlightFilter, FlightImportResult,
    FlightStatistics, BasicMetrics, ExtendedMetrics, RegionRating
)
from ..services.flight_service import FlightService
from ..services.flights_analytics_service import FlightsAnalyticsService

router = APIRouter(prefix="/flights", tags=["flights"])

@router.post("/import", response_model=FlightImportResult)
async def import_flights(
    file: UploadFile = File(..., description="Excel файл с данными полетов"),
    db: Session = Depends(get_db)
):
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
    service = FlightsAnalyticsService(db)
    return service.get_flights_with_filters(
        skip, limit, region, aircraft_type, operator, registration, date_from, date_to
    )

@router.get("/flights_stats/region/{region_id}")
def flights_stats_region(
    region_id: int,
    start_date: Optional[str] = Query(None, description="Начало диапазона dep_date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конец диапазона dep_date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    service = FlightsAnalyticsService(db)
    return service.get_region_statistics(region_id, start_date, end_date)

@router.get("/flights_stats")
def flights_stats(
    start_date: Optional[str] = Query(None, description="Начало диапазона dep_date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конец диапазона dep_date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    service = FlightsAnalyticsService(db)
    return service.get_general_statistics(start_date, end_date)

@router.get("/api/flights")
def flights_all(db: Session = Depends(get_db)):
    service = FlightsAnalyticsService(db)
    return service.get_all_flights()

@router.get("/api/regions")
def regions_stats(db: Session = Depends(get_db)):
    service = FlightsAnalyticsService(db)
    return service.get_regions_statistics()

@router.get("/api/flight/{sid}")
def get_flight(sid: str, db: Session = Depends(get_db)):
    service = FlightsAnalyticsService(db)
    return service.get_flight_by_sid(sid)

@router.get("/zone/{sid}/geojson")
def get_flight_zone_geojson(sid: str, db: Session = Depends(get_db)):
    service = FlightsAnalyticsService(db)
    return service.get_flight_zone_geojson(sid)

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    service = FlightsAnalyticsService(db)
    return service.health_check()