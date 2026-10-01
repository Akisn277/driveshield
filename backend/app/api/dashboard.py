from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.services.auth import require_fleet_manager
from app.models.alert import Alert
from app.models.anomaly_event import AnomalyEvent
from app.models.vehicle import Vehicle
from app.services.telemetry_service import metrics

router = APIRouter(prefix="/api", tags=["dashboard"], dependencies=[Depends(require_fleet_manager)])


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
    type_rows = db.execute(
        select(AnomalyEvent.anomaly_type, func.count(AnomalyEvent.id))
        .group_by(AnomalyEvent.anomaly_type)
    ).all()
    severity_rows = db.execute(
        select(AnomalyEvent.severity, func.count(AnomalyEvent.id))
        .group_by(AnomalyEvent.severity)
    ).all()
    if db.bind.dialect.name == "postgresql":
        time_bucket = func.date_trunc("hour", AnomalyEvent.detected_at)
    else:
        time_bucket = func.strftime("%Y-%m-%d %H:00", AnomalyEvent.detected_at)
    time_rows = db.execute(
        select(time_bucket, func.count(AnomalyEvent.id))
        .group_by(time_bucket)
        .order_by(time_bucket)
    ).all()
    over_time = []
    for bucket, count in time_rows:
        timestamp = bucket.strftime("%Y-%m-%d %H:00") if hasattr(bucket, "strftime") else str(bucket)
        over_time.append({"time": timestamp, "count": count})
    return {
        "by_type": {anomaly_type: count for anomaly_type, count in type_rows},
        "by_severity": {severity: count for severity, count in severity_rows},
        "over_time": over_time,
    }
