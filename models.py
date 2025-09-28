from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import VARCHAR, TIMESTAMP, DOUBLE_PRECISION, JSONB
from database import Base

class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(10), nullable=False, unique=True)
    area_km2 = Column(DOUBLE_PRECISION)

class Flight(Base):
    __tablename__ = "flights"

    id = Column(VARCHAR, primary_key=True, nullable=False)
    flight_id = Column(VARCHAR(50))
    registration = Column(VARCHAR(50))
    aircraft_type = Column(VARCHAR(50))
    operator = Column(Text)
    departure_lat = Column(DOUBLE_PRECISION)
    departure_lon = Column(DOUBLE_PRECISION)
    arrival_lat = Column(DOUBLE_PRECISION)
    arrival_lon = Column(DOUBLE_PRECISION)
    departure_time = Column(TIMESTAMP(timezone=True))
    arrival_time = Column(TIMESTAMP(timezone=True))
    actual_departure_time = Column(TIMESTAMP(timezone=True))
    actual_arrival_time = Column(TIMESTAMP(timezone=True))
    duration_minutes = Column(Integer)
    min_altitude = Column(Integer)
    max_altitude = Column(Integer)
    center_name = Column(VARCHAR(100))
    region_cartodb_id = Column(Integer)
    region_name_latin = Column(String(255))
    region_id = Column(Integer, ForeignKey("regions.id"))
    raw_shr_message = Column(Text)
    raw_dep_message = Column(Text)
    raw_arr_message = Column(Text)
    sid = Column(VARCHAR(50))
    remarks = Column(Text)
    phone_numbers = Column(Text)
    source_sheet = Column(VARCHAR(50))
    data_format = Column(VARCHAR(20))
    created_at = Column(TIMESTAMP(timezone=True))
    updated_at = Column(TIMESTAMP(timezone=True))
