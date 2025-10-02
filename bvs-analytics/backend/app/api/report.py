from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
import os
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime, timezone
from collections import Counter

from ..core.database import get_db
from ..models.flight import Region
from services.report_service.latex_generator import generate_report

report = APIRouter(prefix="/report", tags=["report"])

@report.get("")
def get_report(
    region_id: Optional[int] = Query(None, description="id региона"),
    start_date: Optional[str] = Query(None, description="Начало диапазона dep_date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конец диапазона dep_date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
    ):
    region_str = ''
    if region_id:
        region_str = db.get(Region, region_id).name
    filename = generate_report(start_date, end_date, region_str if region_str else None, image_dir='')
    if not filename:
        raise HTTPException(status_code=500, detail="File didn't generate properly")
    file_path = f"./storage/{filename}" #random path

    # Check if the file exists
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Send the file
    # The 'filename' parameter sets the name for the downloaded file.
    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=f"{filename}"
    )
