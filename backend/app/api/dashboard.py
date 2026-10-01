from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.models.alert import Alert
from app.models.anomaly_event import AnomalyEvent
from app.models.vehicle import Vehicle
from app.services.telemetry_service import metrics

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/summary")
def summary(db: Session = Depends(get_db)):
    active_alerts = select(func.count(Alert.id)).where(Alert.acknowledged.is_(False)).scalar_subquery()
    critical_alerts = select(func.count(Alert.id)).where(
        Alert.severity == "CRITICAL",
        Alert.acknowledged.is_(False),
    ).scalar_subquery()
    counts = db.execute(
        select(
            select(func.count(Vehicle.id)).scalar_subquery(),
            active_alerts,
            critical_alerts,
        )
    ).one()
    return {
        "vehicles_monitored": counts[0],
        "events_processed": metrics["events_processed"],
        "active_anomalies": counts[1],
        "critical_alerts": counts[2],
    }


@router.get("/analytics/anomalies")
def analytics(db: Session = Depends(get_db)):
    events = db.query(AnomalyEvent).order_by(AnomalyEvent.detected_at.asc()).all()
    types = Counter(event.anomaly_type for event in events)
    severities = Counter(event.severity for event in events)
    by_time = Counter(event.detected_at.strftime("%Y-%m-%d %H:00") for event in events)
    return {"by_type": dict(types), "by_severity": dict(severities), "over_time": [{"time": key, "count": value} for key, value in sorted(by_time.items())]}
