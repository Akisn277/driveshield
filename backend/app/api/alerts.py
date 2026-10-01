from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.models.alert import Alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


def serialize(alert: Alert) -> dict:
    return {"alert_id": alert.alert_id, "vehicle_id": alert.vehicle_id, "anomaly_type": alert.anomaly_type, "severity": alert.severity, "score": alert.score, "message": alert.message, "detected_at": alert.detected_at}


@router.get("")
def list_alerts(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), severity: str | None = None, anomaly_type: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if anomaly_type:
        query = query.filter(Alert.anomaly_type.ilike(f"%{anomaly_type}%"))
    alerts = query.order_by(Alert.detected_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"page": page, "page_size": page_size, "items": [serialize(alert) for alert in alerts]}


@router.get("/recent")
def recent_alerts(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return [serialize(alert) for alert in db.query(Alert).order_by(Alert.detected_at.desc()).limit(limit).all()]
