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
@router.get("/flights_stats/region/{region_id}")
async def flights_stats_region(
    region_id: int,
    start_date: Optional[str] = Query(None, description="Начало диапазона dep_date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конец диапазона dep_date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    # 🗓 Преобразуем строки в date
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    from sqlalchemy import text
    query = "SELECT * FROM flights_new WHERE region_id = :region_id"
    params = {"region_id": region_id}

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
    rows = result.fetchall()
    rows = [dict(row._mapping) for row in rows]

    if not rows:
        raise HTTPException(status_code=404, detail="No flights for this region and date range")

    # === агрегаторы ===
    durations = []
    months = Counter()
    weekdays = Counter()
    times = Counter()
    types = Counter()
    operators = Counter()
    flights = []
    region_name = rows[0]["region_name"]

    # === собираем данные ===
    for r in rows:
        duration = r["duration_min"] or 0
        durations.append(duration)

        # Время старта полёта
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

    # 📊 формируем топ-10 по длительности
    flights.sort(key=lambda x: x["duration_min"] or 0, reverse=True)
    top_10 = flights[:10]

    # 🗓 Человеческие названия
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
        "top": top_10,  # ✅ добавили сюда топ-10 полётов
    }

    return stats



# =============================
# Общая статистика (у тебя уже была переделана под SQLAlchemy)
# =============================
@router.get("/flights_stats")
async def flights_stats(
    start_date: Optional[str] = Query(None, description="Начало диапазона dep_date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конец диапазона dep_date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    # 🗓 Преобразуем строки в объекты date
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

    from sqlalchemy import text
    query = "SELECT * FROM flights_new WHERE 1=1"
    params = {}

    # ✅ Фильтрация по дате
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
    rows_dicts = [dict(row._mapping) for row in rows]

    if not rows_dicts:
        raise HTTPException(status_code=404, detail="No flights found for this date range")

    # === агрегаторы ===
    durations = []
    months = Counter()
    weekdays = Counter()
    times = Counter()
    types = Counter()
    operators = Counter()
    region_stats = {}
    flights_all = []

    # === собираем данные ===
    for r in rows_dicts:
        duration = r["duration_min"] or 0
        durations.append(duration)

        # Время старта полёта
        start_ts = r["start_ts"]
        if start_ts:
            dt = start_ts if isinstance(start_ts, datetime) else datetime.fromisoformat(str(start_ts))
            times[dt.hour] += 1
            weekdays[dt.isoweekday()] += 1
            months[dt.month - 1] += 1

        # Тип и оператор
        types[r["uav_type"] or ""] += 1
        if r["operator"]:
            operators[r["operator"]] += 1

        # ✅ агрегация по регионам
        rid = str(r["region_id"])
        if rid not in region_stats:
            region_stats[rid] = {
                "name": r["region_name"],
                "flights": 0,
                "duration": 0
            }
        region_stats[rid]["flights"] += 1
        region_stats[rid]["duration"] += duration

        # ✈️ для top (опционально)
        zone_data = json.loads(r["zone_data"]) if isinstance(r["zone_data"], str) else r["zone_data"]
        flights_all.append({
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

    # 📈 расчёт avgDuration для каждого региона
    for rid, stats in region_stats.items():
        stats["avgDuration"] = round(stats["duration"] / stats["flights"]) if stats["flights"] else 0

    # 📊 сортируем top по длительности
    flights_all.sort(key=lambda x: x["duration_min"] or 0, reverse=True)
    top = flights_all[:100]

    # 🗓 Человеческие названия месяцев и дней
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    week_names = ["", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

    months_pre = {month_names[m]: months[m] for m in sorted(months)}
    weekdays_pre = {week_names[d]: weekdays[d] for d in sorted(weekdays)}
    times_pre = {f"{h}:00": times[h] for h in sorted(times)}

    # ✅ финальный ответ
    result_data = {
        "duration": sum(durations),
        "avg_duration": sum(durations) / len(durations) if durations else 0,
        "flights": len(durations),
        "month": months_pre,
        "weekdays": weekdays_pre,
        "times": times_pre,
        "types": dict(types),
        "operators": dict(operators),
        "regions": region_stats,
        "top": top
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


@router.get("/zone/{sid}/geojson")
def get_flight_zone_geojson(sid: str, db: Session = Depends(get_db)):
    """
    Получение GeoJSON зоны полета по sid
    """
    # Ищем полет в базе по sid
    result = db.execute(text("SELECT * FROM flights_new WHERE sid = :sid"), {"sid": sid})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Flight not found")

    flight = dict(row._mapping)

    # Обрабатываем zone_data
    zone_data = flight["zone_data"]
    if isinstance(zone_data, str):
        try:
            zone = json.loads(zone_data)
        except json.JSONDecodeError:
            zone = zone_data
    else:
        zone = zone_data

    if not zone:
        return {"type": "FeatureCollection", "features": []}

    return generate_geojson_from_zone(zone)


def generate_geojson_from_zone(zone: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерация GeoJSON из данных зоны
    """
    if not zone:
        return {"type": "FeatureCollection", "features": []}

    zone_type = zone.get('type')

    if zone_type == 'round':
        return generate_round_geojson(zone)
    elif zone_type == 'polygon':
        return generate_polygon_geojson(zone)
    elif 'zones' in zone:
        return generate_multizone_geojson(zone)
    else:
        return {"type": "FeatureCollection", "features": []}


def generate_round_geojson(zone: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерация GeoJSON для круглой зоны
    """
    center = zone.get('center', {})
    latitude = center.get('lat')
    longitude = center.get('lon')
    radius = zone.get('radius', 0)

    if not all([latitude is not None, longitude is not None]):
        return {"type": "FeatureCollection", "features": []}

    # Количество точек для аппроксимации окружности
    points = min(max(10, int(radius / 100)), 1000)  # Адаптивное количество точек

    coordinates = []

    # Коэффициенты преобразования (приближенные)
    lat_per_meter = 1 / 111320.0  # 1 градус широты ≈ 111.32 км
    lon_per_meter = 1 / (111320.0 * math.cos(math.radians(latitude)))  # Зависит от широты

    for i in range(points + 1):
        angle = 2 * math.pi * i / points

        # Смещение в метрах
        dx = radius * math.cos(angle)
        dy = radius * math.sin(angle)

        # Преобразуем в градусы
        point_lat = latitude + dy * lat_per_meter
        point_lon = longitude + dx * lon_per_meter

        coordinates.append([point_lon, point_lat])

    # Замыкаем полигон
    if coordinates and coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])

    return {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [coordinates]
                },
                'properties': {
                    'center': [longitude, latitude],
                    'radius': radius
                }
            }
        ]
    }


def generate_polygon_geojson(zone: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерация GeoJSON для полигональной зоны
    """
    zone_data = zone.get('data', {})
    coordinates_data = zone_data.get('coordinates', [])

    if not coordinates_data:
        return {"type": "FeatureCollection", "features": []}

    coordinates = []
    for coord in coordinates_data:
        if isinstance(coord, dict):
            # Формат: {'lat': x, 'lon': y}
            coordinates.append([coord.get('lon', 0), coord.get('lat', 0)])
        elif isinstance(coord, list) and len(coord) >= 2:
            # Формат: [lon, lat] или [lat, lon]
            if isinstance(coord[0], (int, float)) and isinstance(coord[1], (int, float)):
                coordinates.append([float(coord[0]), float(coord[1])])

    # Замыкаем полигон, если последняя точка не совпадает с первой
    if coordinates and coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])

    return {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [coordinates]
                },
                'properties': {
                    'zone': 'zone'
                }
            }
        ]
    }


def generate_multizone_geojson(zone: Dict[str, Any]) -> Dict[str, Any]:
    """
    Генерация GeoJSON для множественных зон
    """
    zones = zone.get('zones', [])
    features = []

    for zone_item in zones:
        zone_type = zone_item.get('type')

        if zone_type == 'polygon' and 'coordinates' in zone_item:
            coordinates_data = zone_item['coordinates']
            coordinates = []

            for coord in coordinates_data:
                if isinstance(coord, list) and len(coord) >= 2:
                    # Предполагаем формат [lat, lon] или [lon, lat]
                    # Определяем порядок координат по величинам
                    if abs(coord[0]) <= 180 and abs(coord[1]) <= 90:
                        # Вероятно [lon, lat]
                        coordinates.append([float(coord[0]), float(coord[1])])
                    else:
                        # Вероятно [lat, lon] - меняем местами
                        coordinates.append([float(coord[1]), float(coord[0])])

            # Замыкаем полигон
            if coordinates and coordinates[0] != coordinates[-1]:
                coordinates.append(coordinates[0])

            if len(coordinates) >= 3:  # Минимум 3 точки для полигона
                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [coordinates]
                    },
                    'properties': {
                        'zone': 'zone'
                    }
                })

        elif zone_type == 'circle' and 'center' in zone_item and 'radius' in zone_item:
            center = zone_item['center']
            radius = zone_item['radius'] * 1000  # км в метры

            if isinstance(center, list) and len(center) >= 2:
                # Определяем порядок координат
                if abs(center[0]) <= 180 and abs(center[1]) <= 90:
                    longitude, latitude = center[0], center[1]
                else:
                    latitude, longitude = center[0], center[1]

                points = min(max(10, int(radius / 100)), 1000)
                circle_coordinates = []

                # Коэффициенты преобразования
                lat_per_meter = 1 / 111320.0
                lon_per_meter = 1 / (111320.0 * math.cos(math.radians(latitude)))

                for i in range(points + 1):
                    angle = 2 * math.pi * i / points

                    dx = radius * math.cos(angle)
                    dy = radius * math.sin(angle)

                    point_lat = latitude + dy * lat_per_meter
                    point_lon = longitude + dx * lon_per_meter

                    circle_coordinates.append([point_lon, point_lat])

                # Замыкаем полигон
                if circle_coordinates and circle_coordinates[0] != circle_coordinates[-1]:
                    circle_coordinates.append(circle_coordinates[0])

                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [circle_coordinates]
                    },
                    'properties': {
                        'center': [longitude, latitude],
                        'radius': radius
                    }
                })

    return {
        'type': 'FeatureCollection',
        'features': features
    }

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
