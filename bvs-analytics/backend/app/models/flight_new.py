# test_analytics.py
from sqlalchemy import create_engine, Column, Integer, String, Date, Time, DateTime, DECIMAL, Text, func, extract, JSON
from datetime import date, time, datetime, timedelta

from sqlalchemy.dialects.postgresql import JSONB
from ..core.config import settings

from ..core.database import Base


# Модель SQLAlchemy
class FlightNew(Base):
    __tablename__ = 'flights_new'

    id = Column(Integer, primary_key=True, index=True)
    sid = Column(String(50), nullable=False)
    center_name = Column(String(255))
    uav_type = Column(String(100))
    operator = Column(String(255))

    # Вылет
    dep_date = Column(Date)
    dep_time = Column(Time)
    dep_lat = Column(DECIMAL(9, 6))
    dep_lon = Column(DECIMAL(9, 6))
    dep_aerodrome_code = Column(String(10))
    dep_aerodrome_name = Column(String(255))

    # Прилет
    arr_date = Column(Date)
    arr_time = Column(Time)
    arr_lat = Column(DECIMAL(9, 6))
    arr_lon = Column(DECIMAL(9, 6))
    arr_aerodrome_code = Column(String(10))
    arr_aerodrome_name = Column(String(255))

    # Временные метки
    start_ts = Column(DateTime(timezone=True))
    end_ts = Column(DateTime(timezone=True))
    duration_min = Column(Integer)

    # Зона и регион
    zone_data = Column(JSONB if "postgres" in settings.DATABASE_URL else JSON)
    region_id = Column(Integer)
    region_name = Column(String(255))

    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)

