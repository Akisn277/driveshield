from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.schemas.telemetry import TelemetryEvent
from app.services.telemetry_service import process_event

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/telemetry")
def ingest_telemetry(event: TelemetryEvent, db: Session = Depends(get_db)):
    return process_event(event, db)
