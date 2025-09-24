from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

class RegionBase(BaseModel):
    name: str
    code: str
    area_km2: Optional[float] = None

class RegionCreate(RegionBase):
    pass

class Region(RegionBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class FlightBase(BaseModel):
    flight_id: Optional[str] = None
    registration: Optional[str] = None
    aircraft_type: Optional[str] = None
    operator: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    remarks: Optional[str] = None
    # Добавляем поля региона из geojson
    region_cartodb_id: Optional[int] = None
    region_name_latin: Optional[str] = None

class FlightCreate(FlightBase):
    departure_lat: Optional[float] = None
    departure_lon: Optional[float] = None
    arrival_lat: Optional[float] = None
    arrival_lon: Optional[float] = None
    region_id: Optional[int] = None
    raw_shr_message: Optional[str] = None
    raw_dep_message: Optional[str] = None
    raw_arr_message: Optional[str] = None
    sid: Optional[str] = None

class Flight(FlightBase):
    id: str
    departure_lat: Optional[float] = None
    departure_lon: Optional[float] = None
    arrival_lat: Optional[float] = None
    arrival_lon: Optional[float] = None
    region_id: Optional[int] = None
    region: Optional[Region] = None
    sid: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FlightImportResult(BaseModel):
    imported: int
    errors: List[str]
    total_processed: int

class BasicMetrics(BaseModel):
    total_flights: int
    avg_duration_minutes: float
    unique_aircraft: int
    unique_operators: int
    date_range: Dict[str, Optional[datetime]]

class ExtendedMetrics(BaseModel):
    peak_load_per_hour: int
    flight_density_per_1000km2: float
    flights_by_hour: Dict[int, int]
    flights_by_day_of_week: Dict[str, int]
    zero_flight_days: int

class RegionRating(BaseModel):
    region_name: str
    region_code: str
    total_flights: int
    avg_duration_minutes: float
    flight_density: float
    rank: int

class FlightStatistics(BaseModel):
    basic_metrics: BasicMetrics
    extended_metrics: Optional[ExtendedMetrics] = None
    top_regions: List[RegionRating]
    flights_by_month: Dict[str, int]
    flights_by_aircraft_type: Dict[str, int]

class FlightFilter(BaseModel):
    region: Optional[str] = None
    aircraft_type: Optional[str] = None
    operator: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    registration: Optional[str] = None

class CoordinatePoint(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Широта")
    lon: float = Field(..., ge=-180, le=180, description="Долгота")

class FlightPath(BaseModel):
    departure: CoordinatePoint
    arrival: CoordinatePoint
    flight_id: str
    duration_minutes: Optional[int] = None

class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(json|csv|xlsx|png|jpeg)$")
    filters: Optional[FlightFilter] = None
    include_raw_messages: bool = False