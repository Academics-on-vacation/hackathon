from sqlalchemy import Column, String, DateTime, Float, Text, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(10), nullable=False, unique=True)
    area_km2 = Column(Float)
    
    # Для SQLite используем простые координаты, для PostGIS - геометрию
    # geometry = Column(Geometry('MULTIPOLYGON', srid=4326))  # Для PostGIS
    
    flights = relationship("Flight", back_populates="region")

class Flight(Base):
    __tablename__ = "flights"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    flight_id = Column(String(50), index=True)
    registration = Column(String(50), index=True)
    aircraft_type = Column(String(50), index=True)
    operator = Column(Text)
    
    # Координаты как отдельные поля для SQLite
    departure_lat = Column(Float)
    departure_lon = Column(Float)
    arrival_lat = Column(Float)
    arrival_lon = Column(Float)
    
    # Для PostGIS:
    # departure_coords = Column(Geometry('POINT', srid=4326))
    # arrival_coords = Column(Geometry('POINT', srid=4326))
    
    departure_time = Column(DateTime(timezone=True))
    arrival_time = Column(DateTime(timezone=True))
    actual_departure_time = Column(DateTime(timezone=True))  # Фактическое время вылета
    actual_arrival_time = Column(DateTime(timezone=True))    # Фактическое время посадки
    duration_minutes = Column(Integer)  # Длительность в минутах
    
    # Высоты полета (новые поля для 2025.xlsx)
    min_altitude = Column(Integer)  # Минимальная высота в метрах
    max_altitude = Column(Integer)  # Максимальная высота в метрах
    
    # Центр ЕС ОрВД (для формата 2025.xlsx)
    center_name = Column(String(100), index=True)
    
    # Дополнительные поля региона из geojson
    region_cartodb_id = Column(Integer, index=True)  # cartodb_id из geojson
    region_name_latin = Column(String(255))  # name_latin из geojson
    
    region_id = Column(Integer, ForeignKey('regions.id'), index=True)
    region = relationship("Region", back_populates="flights")
    
    # Исходные сообщения
    raw_shr_message = Column(Text)
    raw_dep_message = Column(Text)
    raw_arr_message = Column(Text)
    
    # Дополнительные поля
    sid = Column(String(50))  # System ID
    remarks = Column(Text)
    phone_numbers = Column(Text)  # JSON строка с номерами телефонов
    
    # Метаданные
    source_sheet = Column(String(50))  # Название листа источника
    data_format = Column(String(20), default='2024')  # Формат данных (2024/2025)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FlightStatistics(Base):
    __tablename__ = "flight_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey('regions.id'))
    date = Column(DateTime(timezone=True))
    
    # Базовые метрики
    total_flights = Column(Integer, default=0)
    avg_duration_minutes = Column(Float, default=0.0)
    
    # Расширенные метрики
    peak_load_per_hour = Column(Integer, default=0)
    flight_density_per_1000km2 = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    region = relationship("Region")