from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
from collections import Counter, defaultdict
from fastapi import HTTPException
import json
import math
import logging

from ..schemas.flight import FlightFilter, FlightImportResult
from ..services.flight_service import FlightService

logger = logging.getLogger(__name__)

class FlightsAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def import_flights_from_excel(self, file) -> FlightImportResult:
        """
        Импорт данных полетов из Excel файла.
        Поддерживаемые форматы:
        - Файлы с листами по регионам (формат 2024.xlsx)
        - Агрегированные данные (формат 2025.xlsx)
        """
        if not file.filename.endswith('.xlsx'):
            raise HTTPException(
                status_code=400,
                detail="Поддерживаются только Excel файлы (.xlsx)"
            )
        service = FlightService(self.db)
        result = service.import_from_excel(file)
        return FlightImportResult(
            imported=result['imported'],
            errors=result['errors'],
            total_processed=result['total_processed']
        )

    def get_flights_with_filters(
        self, skip: int, limit: int, region: Optional[str],
        aircraft_type: Optional[str], operator: Optional[str],
        registration: Optional[str], date_from: Optional[date],
        date_to: Optional[date]
    ) -> List:
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
        service = FlightService(self.db)
        return service.get_flights(skip=skip, limit=limit, filters=filters)

    def _parse_date_safe(self, date_str: Optional[str], param_name: str = "date") -> Optional[date]:
        """Безопасный парсинг даты с валидацией и обработкой ошибок"""
        if not date_str:
            return None
        
        try:
            # Пытаемся распарсить дату
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            return parsed_date
        except ValueError as e:
            # Логируем ошибку
            logger.warning(f"Invalid date format for {param_name}: {date_str}, error: {e}")
            
            # Пытаемся исправить некорректную дату (например, 2025-06-31 -> 2025-06-30)
            try:
                parts = date_str.split('-')
                if len(parts) == 3:
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    
                    # Проверяем корректность месяца
                    if month < 1 or month > 12:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Некорректный месяц в {param_name}: {month}. Должен быть от 1 до 12."
                        )
                    
                    # Определяем максимальное количество дней в месяце
                    days_in_month = {
                        1: 31, 2: 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28,
                        3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
                    }
                    
                    max_day = days_in_month[month]
                    
                    # Если день больше максимального, корректируем
                    if day > max_day:
                        logger.info(f"Correcting invalid day {day} to {max_day} for month {month}")
                        day = max_day
                    elif day < 1:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Некорректный день в {param_name}: {day}. Должен быть больше 0."
                        )
                    
                    # Возвращаем исправленную дату
                    return date(year, month, day)
            except (ValueError, IndexError) as parse_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Некорректный формат даты для {param_name}: {date_str}. Ожидается формат YYYY-MM-DD. Ошибка: {str(parse_error)}"
                )
            
            raise HTTPException(
                status_code=400,
                detail=f"Некорректная дата для {param_name}: {date_str}. Ожидается формат YYYY-MM-DD."
            )

    def get_region_statistics(
        self, region_id: int, start_date: Optional[str], end_date: Optional[str]
    ) -> Dict[str, Any]:
        start_dt = self._parse_date_safe(start_date, "start_date")
        end_dt = self._parse_date_safe(end_date, "end_date")
        
        params = {"region_id": region_id}
        date_filter = "WHERE region_id = :region_id"
        if start_dt and end_dt:
            date_filter += " AND dep_date BETWEEN :start_date AND :end_date"
            params["start_date"] = start_dt
            params["end_date"] = end_dt
        elif start_dt:
            date_filter += " AND dep_date >= :start_date"
            params["start_date"] = start_dt
        elif end_dt:
            date_filter += " AND dep_date <= :end_date"
            params["end_date"] = end_dt
        
        # Агрегированные запросы
        # 1. Общая статистика
        general_query = f"""
            SELECT
                COUNT(*) as total_flights,
                SUM(COALESCE(duration_min, 0)) as total_duration,
                AVG(COALESCE(duration_min, 0)) as avg_duration,
                MAX(region_name) as region_name
            FROM flights_new
            {date_filter}
        """
        general_result = self.db.execute(text(general_query), params).fetchone()
        
        if not general_result or general_result.total_flights == 0:
            raise HTTPException(status_code=404, detail="No flights for this region and date range")
        
        # 2. Статистика по часам
        time_query = f"""
            SELECT
                EXTRACT(HOUR FROM start_ts) as hour,
                COUNT(*) as count
            FROM flights_new
            {date_filter} AND start_ts IS NOT NULL
            GROUP BY EXTRACT(HOUR FROM start_ts)
            ORDER BY hour
        """
        time_results = self.db.execute(text(time_query), params).fetchall()
        
        # 3. Статистика по дням недели
        weekday_query = f"""
            SELECT
                EXTRACT(ISODOW FROM start_ts) as weekday,
                COUNT(*) as count
            FROM flights_new
            {date_filter} AND start_ts IS NOT NULL
            GROUP BY EXTRACT(ISODOW FROM start_ts)
            ORDER BY weekday
        """
        weekday_results = self.db.execute(text(weekday_query), params).fetchall()
        
        # 4. Статистика по месяцам
        month_query = f"""
            SELECT
                EXTRACT(MONTH FROM start_ts) as month,
                COUNT(*) as count
            FROM flights_new
            {date_filter} AND start_ts IS NOT NULL
            GROUP BY EXTRACT(MONTH FROM start_ts)
            ORDER BY month
        """
        month_results = self.db.execute(text(month_query), params).fetchall()
        
        # 5. Статистика по типам БПЛА
        type_query = f"""
            SELECT
                uav_type,
                COUNT(*) as count
            FROM flights_new
            {date_filter}
            GROUP BY uav_type
        """
        type_results = self.db.execute(text(type_query), params).fetchall()
        
        # 6. Статистика по операторам
        operator_query = f"""
            SELECT
                operator,
                COUNT(*) as count
            FROM flights_new
            {date_filter} AND operator IS NOT NULL
            GROUP BY operator
        """
        operator_results = self.db.execute(text(operator_query), params).fetchall()
        
        # 7. Топ 10 полетов по длительности
        top_query = f"""
            SELECT *
            FROM flights_new
            {date_filter}
            ORDER BY duration_min DESC NULLS LAST
            LIMIT 10
        """
        top_results = self.db.execute(text(top_query), params).fetchall()
        
        # Формируем результат
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        week_names = ["", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        
        times_dict = {f"{int(row.hour)}:00": row.count for row in time_results}
        weekdays_dict = {week_names[int(row.weekday)]: row.count for row in weekday_results}
        months_dict = {month_names[int(row.month) - 1]: row.count for row in month_results}
        types_dict = {row.uav_type or "": row.count for row in type_results}
        operators_dict = {row.operator: row.count for row in operator_results}
        
        # Топ полетов
        top_flights = []
        for row in top_results:
            r = dict(row._mapping)
            zone_data = json.loads(r["zone_data"]) if isinstance(r["zone_data"], str) else r["zone_data"]
            top_flights.append(self._format_flight_data(r, zone_data))
        
        return {
            "name": general_result.region_name,
            "duration": int(general_result.total_duration) if general_result.total_duration else 0,
            "avg_duration": round(general_result.avg_duration) if general_result.avg_duration else 0,
            "flights": general_result.total_flights,
            "month": months_dict,
            "weekdays": weekdays_dict,
            "types": types_dict,
            "operators": operators_dict,
            "times": times_dict,
            "regions": {
                str(region_id): {
                    "name": general_result.region_name,
                    "flights": general_result.total_flights,
                    "avgDuration": round(general_result.avg_duration) if general_result.avg_duration else 0,
                    "duration": int(general_result.total_duration) if general_result.total_duration else 0,
                }
            },
            "top": top_flights,
        }

    def _process_region_data(self, rows: List[Dict], region_id: int) -> Dict[str, Any]:
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
            flights.append(self._format_flight_data(r, zone_data))
        flights.sort(key=lambda x: x["duration_min"] or 0, reverse=True)
        top_10 = flights[:10]
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        week_names = ["", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        months_pre = {month_names[m]: months[m] for m in sorted(months)}
        weekdays_pre = {week_names[d]: weekdays[d] for d in sorted(weekdays)}
        times_pre = {f"{h}:00": times[h] for h in sorted(times)}
        return {
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
            "top": top_10,
        }

    def get_general_statistics(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Оптимизированная статистика с использованием SQL агрегации"""
        start_dt = self._parse_date_safe(start_date, "start_date")
        end_dt = self._parse_date_safe(end_date, "end_date")
        
        params = {}
        date_filter = "WHERE 1=1"
        if start_dt and end_dt:
            date_filter += " AND dep_date BETWEEN :start_date AND :end_date"
            params = {"start_date": start_dt, "end_date": end_dt}
        elif start_dt:
            date_filter += " AND dep_date >= :start_date"
            params = {"start_date": start_dt}
        elif end_dt:
            date_filter += " AND dep_date <= :end_date"
            params = {"end_date": end_dt}
        
        # Агрегированные запросы для получения статистики
        # 1. Общая статистика
        general_query = f"""
            SELECT
                COUNT(*) as total_flights,
                SUM(COALESCE(duration_min, 0)) as total_duration,
                AVG(COALESCE(duration_min, 0)) as avg_duration
            FROM flights_new
            {date_filter}
        """
        general_result = self.db.execute(text(general_query), params).fetchone()
        
        # 2. Статистика по регионам
        region_query = f"""
            SELECT
                region_id,
                region_name,
                COUNT(*) as flights,
                SUM(COALESCE(duration_min, 0)) as duration,
                AVG(COALESCE(duration_min, 0)) as avg_duration
            FROM flights_new
            {date_filter}
            GROUP BY region_id, region_name
        """
        region_results = self.db.execute(text(region_query), params).fetchall()
        
        # 3. Статистика по часам
        time_query = f"""
            SELECT
                EXTRACT(HOUR FROM start_ts) as hour,
                COUNT(*) as count
            FROM flights_new
            {date_filter} AND start_ts IS NOT NULL
            GROUP BY EXTRACT(HOUR FROM start_ts)
            ORDER BY hour
        """
        time_results = self.db.execute(text(time_query), params).fetchall()
        
        # 4. Статистика по дням недели
        weekday_query = f"""
            SELECT
                EXTRACT(ISODOW FROM start_ts) as weekday,
                COUNT(*) as count
            FROM flights_new
            {date_filter} AND start_ts IS NOT NULL
            GROUP BY EXTRACT(ISODOW FROM start_ts)
            ORDER BY weekday
        """
        weekday_results = self.db.execute(text(weekday_query), params).fetchall()
        
        # 5. Статистика по месяцам
        month_query = f"""
            SELECT
                EXTRACT(MONTH FROM start_ts) as month,
                COUNT(*) as count
            FROM flights_new
            {date_filter} AND start_ts IS NOT NULL
            GROUP BY EXTRACT(MONTH FROM start_ts)
            ORDER BY month
        """
        month_results = self.db.execute(text(month_query), params).fetchall()
        
        # 6. Статистика по типам БПЛА
        type_query = f"""
            SELECT
                uav_type,
                COUNT(*) as count
            FROM flights_new
            {date_filter}
            GROUP BY uav_type
        """
        type_results = self.db.execute(text(type_query), params).fetchall()
        
        # 7. Статистика по операторам
        operator_query = f"""
            SELECT
                operator,
                COUNT(*) as count
            FROM flights_new
            {date_filter} AND operator IS NOT NULL
            GROUP BY operator
        """
        operator_results = self.db.execute(text(operator_query), params).fetchall()
        
        # 8. Топ 100 полетов по длительности
        top_query = f"""
            SELECT *
            FROM flights_new
            {date_filter}
            ORDER BY duration_min DESC NULLS LAST
            LIMIT 100
        """
        top_results = self.db.execute(text(top_query), params).fetchall()
        
        # Формируем результат
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        week_names = ["", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        
        # Обработка результатов
        region_stats = {}
        for row in region_results:
            region_stats[str(row.region_id)] = {
                "name": row.region_name,
                "flights": row.flights,
                "duration": int(row.duration),
                "avgDuration": round(row.avg_duration) if row.avg_duration else 0
            }
        
        times_dict = {f"{int(row.hour)}:00": row.count for row in time_results}
        weekdays_dict = {week_names[int(row.weekday)]: row.count for row in weekday_results}
        months_dict = {month_names[int(row.month) - 1]: row.count for row in month_results}
        types_dict = {row.uav_type or "": row.count for row in type_results}
        operators_dict = {row.operator: row.count for row in operator_results}
        
        # Топ полетов
        top_flights = []
        for row in top_results:
            r = dict(row._mapping)
            zone_data = json.loads(r["zone_data"]) if isinstance(r["zone_data"], str) else r["zone_data"]
            top_flights.append(self._format_flight_data(r, zone_data))
        
        return {
            "duration": int(general_result.total_duration) if general_result.total_duration else 0,
            "avg_duration": round(general_result.avg_duration) if general_result.avg_duration else 0,
            "flights": general_result.total_flights,
            "month": months_dict,
            "weekdays": weekdays_dict,
            "times": times_dict,
            "types": types_dict,
            "operators": operators_dict,
            "regions": region_stats,
            "top": top_flights
        }

    def _process_general_statistics(self, rows_dicts: List[Dict]) -> Dict[str, Any]:
        durations = []
        months = Counter()
        weekdays = Counter()
        times = Counter()
        types = Counter()
        operators = Counter()
        region_stats = {}
        flights_all = []
        for r in rows_dicts:
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
            rid = str(r["region_id"])
            if rid not in region_stats:
                region_stats[rid] = {
                    "name": r["region_name"],
                    "flights": 0,
                    "duration": 0
                }
            region_stats[rid]["flights"] += 1
            region_stats[rid]["duration"] += duration
            zone_data = json.loads(r["zone_data"]) if isinstance(r["zone_data"], str) else r["zone_data"]
            flights_all.append(self._format_flight_data(r, zone_data))
        for rid, stats in region_stats.items():
            stats["avgDuration"] = round(stats["duration"] / stats["flights"]) if stats["flights"] else 0
        flights_all.sort(key=lambda x: x["duration_min"] or 0, reverse=True)
        top = flights_all[:100]
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        week_names = ["", "Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        months_pre = {month_names[m]: months[m] for m in sorted(months)}
        weekdays_pre = {week_names[d]: weekdays[d] for d in sorted(weekdays)}
        times_pre = {f"{h}:00": times[h] for h in sorted(times)}
        return {
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

    def get_all_flights(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        uav_type: Optional[str] = None,
        region_id: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc"
    ) -> Dict[str, Any]:
        """Получение полетов с пагинацией, фильтрацией и сортировкой"""
        # Базовый запрос для подсчета общего количества
        count_query = "SELECT COUNT(*) as total FROM flights_new WHERE 1=1"
        # Запрос с вычислением длительности, если она NULL
        data_query = """
            SELECT *,
                CASE
                    WHEN duration_min IS NULL OR duration_min = 0 THEN
                        EXTRACT(EPOCH FROM (end_ts - start_ts)) / 60
                    ELSE duration_min
                END as calculated_duration
            FROM flights_new
            WHERE 1=1
        """
        params = {}
        
        # Применяем фильтры
        filter_conditions = []
        if search:
            filter_conditions.append("(sid ILIKE :search OR uav_type ILIKE :search OR operator ILIKE :search)")
            params["search"] = f"%{search}%"
        
        if uav_type:
            filter_conditions.append("uav_type = :uav_type")
            params["uav_type"] = uav_type
        
        if region_id is not None:
            filter_conditions.append("region_id = :region_id")
            params["region_id"] = region_id
        
        # Добавляем условия к запросам
        if filter_conditions:
            filter_str = " AND " + " AND ".join(filter_conditions)
            count_query += filter_str
            data_query += filter_str
        
        # Получаем общее количество записей
        total_result = self.db.execute(text(count_query), params).fetchone()
        total_count = total_result[0] if total_result else 0
        
        # Маппинг полей сортировки фронтенда на поля БД
        sort_field_mapping = {
            'sid': 'sid',
            'uav_type': 'uav_type',
            'dep.date': 'start_ts',
            'arr.date': 'end_ts',
            'duration_min': 'calculated_duration',
            'region': 'region_name',
            'operator': 'operator'
        }
        
        # Определяем поле и направление сортировки
        sort_field = sort_field_mapping.get(sort_by, 'start_ts')
        sort_direction = 'ASC' if sort_order == 'asc' else 'DESC'
        
        # Добавляем сортировку и пагинацию
        data_query += f" ORDER BY {sort_field} {sort_direction} LIMIT :limit OFFSET :skip"
        params["limit"] = limit
        params["skip"] = skip
        
        # Получаем данные
        result = self.db.execute(text(data_query), params)
        rows = [dict(row._mapping) for row in result.fetchall()]
        
        flights = []
        for r in rows:
            # Используем вычисленную длительность
            if 'calculated_duration' in r and r['calculated_duration']:
                r['duration_min'] = int(r['calculated_duration'])
            
            zone_data = json.loads(r["zone_data"]) if isinstance(r["zone_data"], str) else r["zone_data"]
            flights.append(self._format_flight_data(r, zone_data))
        
        meta = {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "returned": len(flights),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        return {"meta": meta, "flights": flights}

    def get_regions_statistics(self) -> List[Dict[str, Any]]:
        result = self.db.execute(text("""
            SELECT region_id, region_name, duration_min, start_ts, end_ts
            FROM flights_new
        """))
        rows = [dict(row._mapping) for row in result.fetchall()]
        if not rows:
            raise HTTPException(status_code=404, detail="No flights found")
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
            ts_candidates = [t for t in [r["start_ts"], r["end_ts"]] if t is not None]
            if ts_candidates:
                latest = max(ts_candidates)
                prev = regions[rid]["last_flight"]
                if not prev or latest > prev:
                    regions[rid]["last_flight"] = latest
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
        result_list.sort(key=lambda x: x["flights"], reverse=True)
        return result_list

    def get_flight_by_sid(self, sid: str) -> Dict[str, Any]:
        row = self.db.execute(text("SELECT * FROM flights_new WHERE sid = :sid"), {"sid": sid}).fetchone()
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
        return self._format_flight_data(r, zone)

    def get_flight_zone_geojson(self, sid: str) -> Dict[str, Any]:
        """Получение GeoJSON зоны полета по sid"""
        result = self.db.execute(text("SELECT * FROM flights_new WHERE sid = :sid"), {"sid": sid})
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Flight not found")
        flight = dict(row._mapping)
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
        return self._generate_geojson_from_zone(zone)

    def health_check(self) -> Dict[str, str]:
        """Простейшая проверка состояния сервиса и подключения к БД"""
        try:
            self.db.execute(text("SELECT 1"))
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
        
    def _format_flight_data(self, r: Dict, zone_data: Any) -> Dict[str, Any]:
            return {
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
        }

    def _generate_geojson_from_zone(self, zone: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация GeoJSON из данных зоны"""
        if not zone:
            return {"type": "FeatureCollection", "features": []}
        zone_type = zone.get('type')
        if zone_type == 'circle':
            return self._generate_round_geojson(zone)
        elif zone_type == 'polygon':
            return self._generate_polygon_geojson(zone)
        elif 'zones' in zone:
            return self._generate_multizone_geojson(zone)
        else:
            return {"type": "FeatureCollection", "features": []}

    def _generate_round_geojson(self, zone: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация GeoJSON для круглой зоны"""
        zone = zone.get('data')
        center = zone.get('center', {})
        latitude = center.get('lat')
        longitude = center.get('lon')
        radius = int(zone.get('radius_nm', 0)) * 1000
        if not all([latitude is not None, longitude is not None]):
            return {"type": "FeatureCollection", "features": []}
        points = min(max(10, int(radius / 100)), 1000)
        coordinates = []
        lat_per_meter = 1 / 111320.0
        lon_per_meter = 1 / (111320.0 * math.cos(math.radians(latitude)))
        for i in range(points + 1):
            angle = 2 * math.pi * i / points
            dx = radius * math.cos(angle)
            dy = radius * math.sin(angle)
            point_lat = latitude + dy * lat_per_meter
            point_lon = longitude + dx * lon_per_meter
            coordinates.append([point_lon, point_lat])
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

    def _generate_polygon_geojson(self, zone: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация GeoJSON для полигональной зоны"""
        zone_data = zone.get('data', {})
        coordinates_data = zone_data.get('coordinates', [])
        if not coordinates_data:
            return {"type": "FeatureCollection", "features": []}
        coordinates = []
        for coord in coordinates_data:
            if isinstance(coord, dict):
                coordinates.append([coord.get('lon', 0), coord.get('lat', 0)])
            elif isinstance(coord, list) and len(coord) >= 2:
                if isinstance(coord[0], (int, float)) and isinstance(coord[1], (int, float)):
                    coordinates.append([float(coord[0]), float(coord[1])])
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

    def _generate_multizone_geojson(self, zone: Dict[str, Any]) -> Dict[str, Any]:
        """Генерация GeoJSON для множественных зон"""
        zones = zone.get('zones', [])
        features = []
        for zone_item in zones:
            zone_type = zone_item.get('type')
            if zone_type == 'polygon' and 'coordinates' in zone_item:
                coordinates_data = zone_item['coordinates']
                coordinates = []
                for coord in coordinates_data:
                    if isinstance(coord, list) and len(coord) >= 2:
                        if abs(coord[0]) <= 180 and abs(coord[1]) <= 90:
                            coordinates.append([float(coord[0]), float(coord[1])])
                        else:
                            coordinates.append([float(coord[1]), float(coord[0])])
                if coordinates and coordinates[0] != coordinates[-1]:
                    coordinates.append(coordinates[0])
                if len(coordinates) >= 3:
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
                radius = zone_item['radius'] * 1000
                if isinstance(center, list) and len(center) >= 2:
                    if abs(center[0]) <= 180 and abs(center[1]) <= 90:
                        longitude, latitude = center[0], center[1]
                    else:
                        latitude, longitude = center[0], center[1]
                    points = min(max(10, int(radius / 100)), 1000)
                    circle_coordinates = []
                    lat_per_meter = 1 / 111320.0
                    lon_per_meter = 1 / (111320.0 * math.cos(math.radians(latitude)))
                    for i in range(points + 1):
                        angle = 2 * math.pi * i / points
                        dx = radius * math.cos(angle)
                        dy = radius * math.sin(angle)
                        point_lat = latitude + dy * lat_per_meter
                        point_lon = longitude + dx * lon_per_meter
                        circle_coordinates.append([point_lon, point_lat])
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
