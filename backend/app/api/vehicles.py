import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.models.alert import Alert
from app.models.anomaly_event import AnomalyEvent
from app.models.vehicle import Vehicle
from app.services.auth import require_fleet_manager

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"], dependencies=[Depends(require_fleet_manager)])


def alert_dict(alert: Alert) -> dict:
    return {"alert_id": alert.alert_id, "vehicle_id": alert.vehicle_id, "anomaly_type": alert.anomaly_type, "severity": alert.severity, "score": alert.score, "message": alert.message, "detected_at": alert.detected_at}


@router.get("")
def list_vehicles(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    items = db.query(Vehicle).order_by(Vehicle.vehicle_id).offset((page - 1) * page_size).limit(page_size).all()
    return {"page": page, "page_size": page_size, "items": [{"vehicle_id": v.vehicle_id, "vehicle_type": v.vehicle_type, "latitude": v.latitude, "longitude": v.longitude, "speed": v.speed, "temperature": v.temperature, "battery": v.battery, "fuel_level": v.fuel_level, "ignition": v.ignition, "max_speed": v.max_speed, "active": v.active} for v in items]}


@router.get("/{vehicle_id}")
def vehicle_detail(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    alerts = db.query(Alert).filter(Alert.vehicle_id == vehicle_id).order_by(Alert.detected_at.desc()).limit(20).all()
    anomalies = db.query(AnomalyEvent).filter(AnomalyEvent.vehicle_id == vehicle_id).order_by(AnomalyEvent.detected_at.desc()).limit(20).all()
    latest = alerts[0] if alerts else None
    return {"vehicle": {"vehicle_id": vehicle.vehicle_id, "vehicle_type": vehicle.vehicle_type, "latitude": vehicle.latitude, "longitude": vehicle.longitude, "speed": vehicle.speed, "temperature": vehicle.temperature, "battery": vehicle.battery, "fuel_level": vehicle.fuel_level, "ignition": vehicle.ignition, "max_speed": vehicle.max_speed, "active": vehicle.active}, "anomaly_score": latest.score if latest else 0, "severity": latest.severity if latest else "NORMAL", "reasons": json.loads(anomalies[0].reasons) if anomalies else [], "recent_anomalies": [{"event_id": e.event_id, "score": e.score, "severity": e.severity, "reasons": json.loads(e.reasons), "detected_at": e.detected_at} for e in anomalies], "latest_alerts": [alert_dict(alert) for alert in alerts]}
