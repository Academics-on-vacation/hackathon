from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, extract
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging
from fastapi import UploadFile
import tempfile
import os

from ..models.flight import Flight, Region, FlightStatistics
from ..schemas.flight import FlightCreate, FlightFilter, BasicMetrics, ExtendedMetrics, RegionRating
from parsers.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class FlightService:
    """Сервис для работы с полетами"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_processor = DataProcessor()
    
    async def import_from_excel(self, file: UploadFile) -> Dict[str, Any]:
        """Импорт данных из Excel файла"""
        try:
            # Сохраняем файл временно
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                # Обрабатываем файл
                result = self.data_processor.process_excel_file(tmp_file_path)
                
                imported_count = 0
                errors = result.get('errors', [])
                
                # Сохраняем полеты в БД
                for flight_data in result.get('flights', []):
                    try:
                        # Находим или создаем регион
                        region = self._get_or_create_region(flight_data.get('region_name'))
                        
                        # Создаем запись полета
                        flight_record = self.data_processor.create_flight_record(flight_data)
                        if region:
                            flight_record['region_id'] = region.id
                        
                        # Создаем объект полета
                        flight = Flight(**flight_record)
                        self.db.add(flight)
                        imported_count += 1
                        
                    except Exception as e:
                        error_msg = f"Error saving flight: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                # Сохраняем изменения
                self.db.commit()
                
                logger.info(f"Successfully imported {imported_count} flights")
                
                return {
                    'imported': imported_count,
                    'errors': errors,
                    'total_processed': result.get('total_processed', 0),
                    'sheets_processed': result.get('sheets_processed', 0)
                }
                
            finally:
                # Удаляем временный файл
                os.unlink(tmp_file_path)
                
        except Exception as e:
            logger.error(f"Error importing Excel file: {e}")
            return {
                'imported': 0,
                'errors': [f"Import failed: {str(e)}"],
                'total_processed': 0,
                'sheets_processed': 0
            }
    
    def get_flights(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[FlightFilter] = None
    ) -> List[Flight]:
        """Получение списка полетов с фильтрацией"""
        query = self.db.query(Flight)
        
        if filters:
            if filters.region:
                query = query.join(Region).filter(Region.name.ilike(f"%{filters.region}%"))
            
            if filters.aircraft_type:
                query = query.filter(Flight.aircraft_type.ilike(f"%{filters.aircraft_type}%"))
            
            if filters.operator:
                query = query.filter(Flight.operator.ilike(f"%{filters.operator}%"))
            
            if filters.registration:
                query = query.filter(Flight.registration.ilike(f"%{filters.registration}%"))
            
            if filters.date_from:
                query = query.filter(Flight.departure_time >= filters.date_from)
            
            if filters.date_to:
                query = query.filter(Flight.departure_time <= filters.date_to)
        
        return query.order_by(desc(Flight.departure_time)).offset(skip).limit(limit).all()
    
    def get_flight_by_id(self, flight_id: str) -> Optional[Flight]:
        """Получение полета по ID"""
        return self.db.query(Flight).filter(Flight.id == flight_id).first()
    
    def get_basic_metrics(self, filters: Optional[FlightFilter] = None) -> BasicMetrics:
        """Получение базовых метрик"""
        query = self.db.query(Flight)
        
        # Применяем фильтры
        if filters:
            query = self._apply_filters(query, filters)
        
        flights = query.all()
        
        if not flights:
            return BasicMetrics(
                total_flights=0,
                avg_duration_minutes=0.0,
                unique_aircraft=0,
                unique_operators=0,
                date_range={'min': None, 'max': None}
            )
        
        # Вычисляем метрики
        total_flights = len(flights)
        
        # Средняя длительность
        durations = [f.duration_minutes for f in flights if f.duration_minutes]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        # Уникальные БВС и операторы
        unique_aircraft = len(set(f.registration for f in flights if f.registration))
        unique_operators = len(set(f.operator for f in flights if f.operator))
        
        # Диапазон дат
        departure_times = [f.departure_time for f in flights if f.departure_time]
        date_range = {
            'min': min(departure_times) if departure_times else None,
            'max': max(departure_times) if departure_times else None
        }
        
        return BasicMetrics(
            total_flights=total_flights,
            avg_duration_minutes=round(avg_duration, 2),
            unique_aircraft=unique_aircraft,
            unique_operators=unique_operators,
            date_range=date_range
        )
    
    def get_extended_metrics(self, filters: Optional[FlightFilter] = None) -> ExtendedMetrics:
        """Получение расширенных метрик"""
        query = self.db.query(Flight)
        
        if filters:
            query = self._apply_filters(query, filters)
        
        flights = query.all()
        
        if not flights:
            return ExtendedMetrics(
                peak_load_per_hour=0,
                flight_density_per_1000km2=0.0,
                flights_by_hour={},
                flights_by_day_of_week={},
                zero_flight_days=0
            )
        
        # Пиковая нагрузка по часам
        hourly_flights = {}
        daily_flights = {}
        
        for flight in flights:
            if flight.departure_time:
                hour = flight.departure_time.hour
                day = flight.departure_time.date()
                
                hourly_flights[hour] = hourly_flights.get(hour, 0) + 1
                daily_flights[day] = daily_flights.get(day, 0) + 1
        
        peak_load = max(hourly_flights.values()) if hourly_flights else 0
        
        # Распределение по дням недели
        weekday_flights = {}
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        
        for flight in flights:
            if flight.departure_time:
                weekday = weekdays[flight.departure_time.weekday()]
                weekday_flights[weekday] = weekday_flights.get(weekday, 0) + 1
        
        # Дни без полетов
        if daily_flights:
            date_range = max(daily_flights.keys()) - min(daily_flights.keys())
            total_days = date_range.days + 1
            flight_days = len(daily_flights)
            zero_flight_days = total_days - flight_days
        else:
            zero_flight_days = 0
        
        return ExtendedMetrics(
            peak_load_per_hour=peak_load,
            flight_density_per_1000km2=0.0,  # Требует данных о площади регионов
            flights_by_hour=hourly_flights,
            flights_by_day_of_week=weekday_flights,
            zero_flight_days=zero_flight_days
        )
    
    def get_regions_rating(
        self, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None
    ) -> List[RegionRating]:
        """Получение рейтинга регионов по активности"""
        query = self.db.query(
            Region.name,
            Region.code,
            Region.area_km2,
            func.count(Flight.id).label('total_flights'),
            func.avg(Flight.duration_minutes).label('avg_duration')
        ).outerjoin(Flight)
        
        if date_from:
            query = query.filter(Flight.departure_time >= date_from)
        if date_to:
            query = query.filter(Flight.departure_time <= date_to)
        
        results = query.group_by(Region.id, Region.name, Region.code, Region.area_km2)\
                      .order_by(desc('total_flights')).all()
        
        ratings = []
        for rank, result in enumerate(results, 1):
            flight_density = 0.0
            if result.area_km2 and result.total_flights:
                flight_density = (result.total_flights / result.area_km2) * 1000
            
            ratings.append(RegionRating(
                region_name=result.name,
                region_code=result.code or '',
                total_flights=result.total_flights or 0,
                avg_duration_minutes=round(result.avg_duration or 0.0, 2),
                flight_density=round(flight_density, 4),
                rank=rank
            ))
        
        return ratings
    
    def get_flights_by_month(self, filters: Optional[FlightFilter] = None) -> Dict[str, int]:
        """Получение количества полетов по месяцам"""
        query = self.db.query(
            extract('year', Flight.departure_time).label('year'),
            extract('month', Flight.departure_time).label('month'),
            func.count(Flight.id).label('count')
        ).filter(Flight.departure_time.isnot(None))
        
        if filters:
            query = self._apply_filters(query, filters)
        
        results = query.group_by('year', 'month').order_by('year', 'month').all()
        
        monthly_data = {}
        for result in results:
            month_key = f"{int(result.year)}-{int(result.month):02d}"
            monthly_data[month_key] = result.count
        
        return monthly_data
    
    def get_flights_by_aircraft_type(self, filters: Optional[FlightFilter] = None) -> Dict[str, int]:
        """Получение количества полетов по типам БВС"""
        query = self.db.query(
            Flight.aircraft_type,
            func.count(Flight.id).label('count')
        ).filter(Flight.aircraft_type.isnot(None))
        
        if filters:
            query = self._apply_filters(query, filters)
        
        results = query.group_by(Flight.aircraft_type).order_by(desc('count')).all()
        
        return {result.aircraft_type: result.count for result in results}
    
    def _apply_filters(self, query, filters: FlightFilter):
        """Применяет фильтры к запросу"""
        if filters.region:
            query = query.join(Region).filter(Region.name.ilike(f"%{filters.region}%"))
        
        if filters.aircraft_type:
            query = query.filter(Flight.aircraft_type.ilike(f"%{filters.aircraft_type}%"))
        
        if filters.operator:
            query = query.filter(Flight.operator.ilike(f"%{filters.operator}%"))
        
        if filters.registration:
            query = query.filter(Flight.registration.ilike(f"%{filters.registration}%"))
        
        if filters.date_from:
            query = query.filter(Flight.departure_time >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(Flight.departure_time <= filters.date_to)
        
        return query
    
    def _get_or_create_region(self, region_name: str) -> Optional[Region]:
        """Находит или создает регион"""
        if not region_name:
            return None
        
        # Ищем существующий регион
        region = self.db.query(Region).filter(Region.name == region_name).first()
        
        if not region:
            # Создаем новый регион
            region = Region(
                name=region_name,
                code=region_name[:10],  # Простой код из названия
                area_km2=None  # Будет заполнено позже из шейп-файлов
            )
            self.db.add(region)
            self.db.flush()  # Получаем ID без коммита
        
        return region
    
    def get_flight_statistics_summary(self, filters: Optional[FlightFilter] = None) -> Dict[str, Any]:
        """Получение сводной статистики"""
        basic_metrics = self.get_basic_metrics(filters)
        extended_metrics = self.get_extended_metrics(filters)
        top_regions = self.get_regions_rating()[:10]  # Топ-10 регионов
        flights_by_month = self.get_flights_by_month(filters)
        flights_by_aircraft_type = self.get_flights_by_aircraft_type(filters)
        
        return {
            'basic_metrics': basic_metrics,
            'extended_metrics': extended_metrics,
            'top_regions': top_regions,
            'flights_by_month': flights_by_month,
            'flights_by_aircraft_type': flights_by_aircraft_type
        }