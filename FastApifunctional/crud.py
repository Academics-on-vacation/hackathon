from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models import Flight, Region
from typing import List, Optional
from schemas import FlightCreate, RegionCreate

async def get_regions(db: AsyncSession) -> List[Region]:
    q = await db.execute(select(Region))
    return q.scalars().all()

async def get_region(db: AsyncSession, region_id: int) -> Optional[Region]:
    q = await db.execute(select(Region).where(Region.id == region_id))
    return q.scalars().first()

async def create_region(db: AsyncSession, region: RegionCreate) -> Region:
    db_obj = Region(**region.dict())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_flights(db: AsyncSession, limit: int = 100, offset: int = 0, registration: Optional[str] = None):
    q = select(Flight)
    if registration:
        q = q.where(Flight.registration == registration)
    q = q.limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()

async def get_flight(db: AsyncSession, flight_id: str):
    q = await db.execute(select(Flight).where(Flight.id == flight_id))
    return q.scalars().first()

async def create_flight(db: AsyncSession, flight: FlightCreate):
    db_obj = Flight(**flight.dict())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def update_flight(db: AsyncSession, flight_id: str, values: dict):
    await db.execute(update(Flight).where(Flight.id == flight_id).values(**values))
    await db.commit()
    return await get_flight(db, flight_id)

async def delete_flight(db: AsyncSession, flight_id: str):
    await db.execute(delete(Flight).where(Flight.id == flight_id))
    await db.commit()
    return True
