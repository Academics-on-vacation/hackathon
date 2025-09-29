from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class RegionBase(BaseModel):
    name: str
    code: str
    area_km2: Optional[float] = None

class RegionCreate(RegionBase):
    pass

class RegionOut(RegionBase):
    id: int
    class Config:
        orm_mode = True

class FlightBase(BaseModel):
    id: str
    flight_id: Optional[str] = None
    registration: Optional[str] = None
    aircraft_type: Optional[str] = None
    operator: Optional[str] = None
    departure_lat: Optional[float]
    departure_lon: Optional[float]
    arrival_lat: Optional[float]
    arrival_lon: Optional[float]
    departure_time: Optional[datetime]
    arrival_time: Optional[datetime]
    duration_minutes: Optional[int]
    min_altitude: Optional[int]
    max_altitude: Optional[int]
    center_name: Optional[str]
    region_cartodb_id: Optional[int]
    region_name_latin: Optional[str]
    region_id: Optional[int]
    raw_shr_message: Optional[str]
    raw_dep_message: Optional[str]
    raw_arr_message: Optional[str]
    sid: Optional[str]
    remarks: Optional[str]
    phone_numbers: Optional[str]
    source_sheet: Optional[str]
    data_format: Optional[str]

class FlightCreate(FlightBase):
    pass

class FlightUpdate(BaseModel):
    # частичное обновление — все поля опциональны
    flight_id: Optional[str] = None
    registration: Optional[str] = None
    # ... при необходимости добавь остальные поля
    class Config:
        orm_mode = True

class FlightOut(FlightBase):
    class Config:
        orm_mode = True
