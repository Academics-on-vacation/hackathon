from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
from collections import Counter
import json

from ..core.database import get_db
from ..schemas.flight import (
    Flight, FlightCreate, FlightFilter, FlightImportResult,
    FlightStatistics, BasicMetrics, ExtendedMetrics, RegionRating
)
from ..services.flight_service import FlightService

router = APIRouter(prefix="/flights", tags=["flights"])


# =============================
# Импорт полётов из Excel
# =============================
@router.post("/import", response_model=FlightImportResult)
async def import_flights(
    file: UploadFile = File(..., description="Excel файл с данными полетов"),
    db: Session = Depends(get_db)
):
    """
    Импорт данных полетов из Excel файла.

    Поддерживаемые форматы:
    - Файлы с листами по регионам (формат 2024.xlsx)
    - Агрегированные данные (формат 2025.xlsx)

    ВАЖНО: эндпоинт остаётся async, т.к. сервис может быть асинхронным.
    Доступ к БД тут идёт через синхронный SQLAlchemy Session (db), что ОК,
    пока мы не вызываем async-методы у сессии.
    """
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="Поддерживаются только Excel файлы (.xlsx)"
        )

    service = FlightService(db)
    # Предполагаем, что метод сервиса асинхронный — поэтому await оставляем.
    result = await service.import_from_excel(file)

    return FlightImportResult(
        imported=result['imported'],
        errors=result['errors'],
        total_processed=result['total_processed']
    )


# =============================
# Список полётов с фильтрами
# =============================
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
    Получение списка полетов с фильтрацией.

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


# =============================
# Статистика по региону
# (SQLAlchemy, синхронно)
# =============================
@router.get("/api/flights_stats/region/{region_id}")
def flights_stats_region(
    region_id: int,
    start_date: Optional[str] = Query(None, description="Начало диапазона dep_date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конец диапазона dep_date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    # Преобразуем строки в date
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    # Строим SQL с параметрами
    query = "SELECT * FROM flights_new WHERE region_id = :region_id"
    params: Dict[str, Any] = {"region_id": region_id}

    if start_dt and end_dt:
        query += " AND dep_date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_dt
        params["end_date"] = end_dt
    elif start_dt:
        query += " AND dep_date >= :start_date"
        params["start_date"] = start_dt
    elif end_dt:
        query += " AND dep_date <= :end_date"
        params["end_date"] = end_dt

    result = db.execute(text(query), params)
    rows = [dict(row._mapping) for row in result.fetchall()]

    if not rows:
        raise HTTPException(status_code=404, detail="No flights for this region and date range")

    # === сбор статистики ===
    durations = []
    months = Counter()
    weekdays = Counter()
    times = Counter()
    types = Counter()
    operators = Counter()
    flights = []
    region_name = rows[0]["region_name"]

    for r in rows:
        duration = r["duration_min"] or 0
        durations.append(duration)

        start_ts = r["start_ts"]
        if start_ts:
            dt = start_ts if isinstance(start_ts, datetime) else datetime.fromisoformat(str(start_ts))
            times[dt.hour] += 1
            weekdays[dt.isoweekday()] += 1
            months[dt.month - 1] += 1

        types[r["uav_type"] or ""] += 1
        if r["operator"]:
            operators[r["operator"]] += 1

        zone_data = json.loads(r["zone_data"]) if isinstance(r["zone_data"], str) else r["zone_data"]
        flights.append({
            "sid": r["sid"],
            "center_name": r["center_name"],
            "uav_type": r["uav_type"],
            "operator": r["operator"],
            "zone": zone_data,
            "dep": {
                "date": r["dep_date"].isoformat() if r["dep_date"] else None,
                "time_hhmm": r["dep_time"].strftime("%H%M") if r["dep_time"] else None,
                "lat": r["dep_lat"],
                "lon": r["dep_lon"],
                "aerodrome_code": r["dep_aerodrome_code"],
                "aerodrome_name": r["dep_aerodrome_name"],
            },
            "arr": {
                "date": r["arr_date"].isoformat() if r["arr_date"] else None,
                "time_hhmm": r["arr_time"].strftime("%H%M") if r["arr_time"] else None,
                "lat": r["arr_lat"],
                "lon": r["arr_lon"],
                "aerodrome_code": r["arr_aerodrome_code"],
                "aerodrome_name": r["arr_aerodrome_name"],
            },
            "start_ts": r["start_ts"].isoformat() if r["start_ts"] else None,
            "end_ts": r["end_ts"].isoformat() if r["end_ts"] else None,
            "duration_min": r["duration_min"],
            "region_id": r["region_id"],
            "region_name": r["region_name"],
        })

    flights.sort(key=lambda x: x["duration_min"] or 0, reverse=True)
    top = flights[:100]

    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    week_names = ["", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    months_pre = {month_names[m]: months[m] for m in sorted(months)}
    weekdays_pre = {week_names[d]: weekdays[d] for d in sorted(weekdays)}
    times_pre = {f"{h}:00": times[h] for h in sorted(times)}

    stats = {
        "name": region_name,
        "duration": sum(durations),
        "avg_duration": sum(durations) / len(durations) if durations else 0,
        "flights": len(durations),
        "month": months_pre,
        "weekdays": weekdays_pre,
        "types": dict(types),
        "operators": dict(operators),
        "times": times_pre,
        "regions": {
            str(region_id): {
                "name": region_name,
                "flights": len(durations),
                "avgDuration": sum(durations) / len(durations) if durations else 0,
                "duration": sum(durations),
            }
        },
        "top": top,
    }

    return stats


# =============================
# Общая статистика (у тебя уже была переделана под SQLAlchemy)
# =============================
@router.get("/flights_stats")
def flights_stats(
    start_date: Optional[str] = Query(None, description="Начало диапазона dep_date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конец диапазона dep_date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    query = "SELECT * FROM flights_new WHERE 1=1"
    params: Dict[str, Any] = {}

    if start_dt and end_dt:
        query += " AND dep_date BETWEEN :start_date AND :end_date"
        params = {"start_date": start_dt, "end_date": end_dt}
    elif start_dt:
        query += " AND dep_date >= :start_date"
        params = {"start_date": start_dt}
    elif end_dt:
        query += " AND dep_date <= :end_date"
        params = {"end_date": end_dt}

    result = db.execute(text(query), params)
    rows = result.fetchall()

    # Приводим строки к dict, чтобы работать одинаково
    rows_dicts = [dict(row._mapping) for row in rows]

    if not rows_dicts:
        raise HTTPException(status_code=404, detail="No flights found for this date range")

    durations = []
    types = Counter()
    operators = Counter()
    regions = Counter()

    for r in rows_dicts:
        durations.append(r["duration_min"] or 0)
        types[r["uav_type"] or ""] += 1
        if r["operator"]:
            operators[r["operator"]] += 1
        regions[r["region_name"]] += 1

    result_data = {
        "duration": sum(durations),
        "avg_duration": sum(durations) / len(durations) if durations else 0,
        "flights": len(durations),
        "types": dict(types),
        "operators": dict(operators),
        "regions": dict(regions)
    }

    return result_data


# =============================
# Все полёты (списком) — SQLAlchemy
# =============================
@router.get("/api/flights")
def flights_all(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM flights_new"))
    rows = [dict(row._mapping) for row in result.fetchall()]

    if not rows:
        raise HTTPException(status_code=404, detail="No flights found")

    flights = []
    for r in rows:
        # zone_data может быть JSON-строкой или уже dict
        zone_data = json.loads(r["zone_data"]) if isinstance(r["zone_data"], str) else r["zone_data"]

        flights.append({
            "sid": r["sid"],
            "center_name": r["center_name"],
            "uav_type": r["uav_type"],
            "operator": r["operator"],
            "zone": zone_data,
            "dep": {
                "date": r["dep_date"].isoformat() if r["dep_date"] else None,
                "time_hhmm": r["dep_time"].strftime("%H%M") if r["dep_time"] else None,
                "lat": r["dep_lat"],
                "lon": r["dep_lon"],
                "aerodrome_code": r["dep_aerodrome_code"],
                "aerodrome_name": r["dep_aerodrome_name"],
            },
            "arr": {
                "date": r["arr_date"].isoformat() if r["arr_date"] else None,
                "time_hhmm": r["arr_time"].strftime("%H%M") if r["arr_time"] else None,
                "lat": r["arr_lat"],
                "lon": r["arr_lon"],
                "aerodrome_code": r["arr_aerodrome_code"],
                "aerodrome_name": r["arr_aerodrome_name"],
            },
            "start_ts": r["start_ts"].isoformat() if r["start_ts"] else None,
            "end_ts": r["end_ts"].isoformat() if r["end_ts"] else None,
            "duration_min": r["duration_min"],
            "region_id": r["region_id"],
            "region_name": r["region_name"],
        })

    meta = {
        "source_excel": "2025.xlsx",   # при желании вынести в конфиг/ENV
        "sheet": "Result_1",
        "parsed_rows": len(rows),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    return {"meta": meta, "flights": flights}


# =============================
# Регионы с агрегатной статистикой — SQLAlchemy
# =============================
@router.get("/api/regions")
def regions_stats(db: Session = Depends(get_db)):
    result = db.execute(text("""
        SELECT region_id, region_name, duration_min, start_ts, end_ts
        FROM flights_new
    """))
    rows = [dict(row._mapping) for row in result.fetchall()]

    if not rows:
        raise HTTPException(status_code=404, detail="No flights found")

    from collections import defaultdict

    # Агрегация по регионам
    regions = defaultdict(lambda: {
        "region_id": None,
        "name": None,
        "flights": 0,
        "duration_sum": 0,
        "last_flight": None,
    })

    for r in rows:
        rid = r["region_id"]
        name = r["region_name"]

        regions[rid]["region_id"] = rid
        regions[rid]["name"] = name
        regions[rid]["flights"] += 1
        regions[rid]["duration_sum"] += r["duration_min"] or 0

        # последний полёт — максимум по start_ts/end_ts
        ts_candidates = [t for t in [r["start_ts"], r["end_ts"]] if t is not None]
        if ts_candidates:
            latest = max(ts_candidates)
            prev = regions[rid]["last_flight"]
            if not prev or latest > prev:
                regions[rid]["last_flight"] = latest

    # Приводим к финальному списку
    result_list = []
    for rid, data in regions.items():
        flights_count = data["flights"]
        avg_duration = data["duration_sum"] / flights_count if flights_count else 0
        result_list.append({
            "region_id": data["region_id"],
            "name": data["name"],
            "flights": flights_count,
            "avgDuration": round(avg_duration, 1),
            "duration": data["duration_sum"],
            "last_flight": data["last_flight"].astimezone(timezone.utc).isoformat() if data["last_flight"] else None
        })

    # Сортировка по количеству полётов (как в твоём примере)
    result_list.sort(key=lambda x: x["flights"], reverse=True)

    return result_list


# =============================
# Один полёт по sid — SQLAlchemy
# =============================
@router.get("/api/flight/{sid}")
def get_flight(sid: str, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM flights_new WHERE sid = :sid"), {"sid": sid}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Flight not found")

    r = dict(row._mapping)

    zone_data = r["zone_data"]
    if isinstance(zone_data, str):
        try:
            zone = json.loads(zone_data)
        except json.JSONDecodeError:
            zone = zone_data
    else:
        zone = zone_data

    flight = {
        "sid": r["sid"],
        "center_name": r["center_name"],
        "uav_type": r["uav_type"],
        "operator": r["operator"],
        "zone": zone,
        "dep": {
            "date": r["dep_date"].isoformat() if r["dep_date"] else None,
            "time_hhmm": r["dep_time"].strftime("%H%M") if r["dep_time"] else None,
            "lat": r["dep_lat"],
            "lon": r["dep_lon"],
            "aerodrome_code": r["dep_aerodrome_code"],
            "aerodrome_name": r["dep_aerodrome_name"],
        },
        "arr": {
            "date": r["arr_date"].isoformat() if r["arr_date"] else None,
            "time_hhmm": r["arr_time"].strftime("%H%M") if r["arr_time"] else None,
            "lat": r["arr_lat"],
            "lon": r["arr_lon"],
            "aerodrome_code": r["arr_aerodrome_code"],
            "aerodrome_name": r["arr_aerodrome_name"],
        },
        "start_ts": r["start_ts"].isoformat() if r["start_ts"] else None,
        "end_ts": r["end_ts"].isoformat() if r["end_ts"] else None,
        "duration_min": r["duration_min"],
        "region_id": r["region_id"],
        "region_name": r["region_name"],
    }

    return flight


# =============================
# Healthcheck — SQLAlchemy
# =============================
@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Простейшая проверка состояния сервиса и подключения к БД"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
