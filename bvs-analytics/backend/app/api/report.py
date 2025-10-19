from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
import os
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..models.flight import Region
from ..services.latex_generator import generate_report

report = APIRouter(prefix="/report", tags=["report"])

@report.get("")
def get_report(
    start_date: Optional[str] = Query(None, description="Начало диапазона dep_date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Конец диапазона dep_date (YYYY-MM-DD)"),
    region_id: Optional[int] = Query(None, description="id региона"),
    db: Session = Depends(get_db)
    ):
    filename = generate_report(db, start_date, end_date, region_id)
    if not filename:
        raise HTTPException(status_code=500, detail="File didn't generate properly")

    # Check if the file exists
    if not os.path.isfile(filename):
        raise HTTPException(status_code=404, detail="File not found")

    # Send the file
    # The 'filename' parameter sets the name for the downloaded file.
    return FileResponse(
        path=filename,
        media_type='application/octet-stream',
        filename=f"{filename}"
    )
