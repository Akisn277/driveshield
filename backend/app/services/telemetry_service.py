import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.mongo import telemetry_collection
from app.models.alert import Alert
from app.models.anomaly_event import AnomalyEvent
from app.models.vehicle import Vehicle
from app.schemas.telemetry import TelemetryEvent
from app.services.anomaly_detector import detect_anomalies

logger = logging.getLogger("driveshield")
processed_event_ids: set[str] = set()
metrics = {"events_processed": 0, "events_rejected": 0, "duplicates": 0, "active_anomalies": 0}


def process_event(event: TelemetryEvent, db: Session) -> dict:
    if event.event_id in processed_event_ids:
        metrics["duplicates"] += 1
        logger.info("duplicate event_id=%s vehicle_id=%s", event.event_id, event.vehicle_id)
        return {"status": "duplicate", "event_id": event.event_id}

    processed_event_ids.add(event.event_id)
    if len(processed_event_ids) > 200000:
        processed_event_ids.clear()

    try:
        telemetry_collection.insert_one(event.model_dump(mode="json"))
    except Exception as exc:
        logger.warning("telemetry storage error event_id=%s error=%s", event.event_id, exc)

    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == event.vehicle_id).first()
    if vehicle is None:
        vehicle = Vehicle(
            vehicle_id=event.vehicle_id,
            vehicle_type="fleet",
            latitude=event.latitude,
            longitude=event.longitude,
            max_speed=100,
        )
        db.add(vehicle)
        db.flush()
    result = detect_anomalies(event, vehicle)
    vehicle.latitude = event.latitude
    vehicle.longitude = event.longitude
    vehicle.speed = event.speed
    vehicle.temperature = event.temperature
    vehicle.battery = event.battery
    vehicle.fuel_level = event.fuel_level
    vehicle.ignition = event.ignition
    db.commit()

    if result.reasons:
        detected_at = event.timestamp.replace(tzinfo=None)
        anomaly_type = ", ".join(result.reasons)
        db.add(AnomalyEvent(
            event_id=event.event_id,
            vehicle_id=event.vehicle_id,
            anomaly_type=anomaly_type,
            score=result.score,
            severity=result.severity,
            reasons=json.dumps(result.reasons),
            detected_at=detected_at,
        ))
        db.add(Alert(
            alert_id=f"alert_{event.event_id}",
            vehicle_id=event.vehicle_id,
            anomaly_type=anomaly_type,
            severity=result.severity,
            score=result.score,
            message="; ".join(result.reasons),
            detected_at=detected_at,
        ))
        metrics["active_anomalies"] += 1
        logger.warning("anomaly detected event_id=%s vehicle_id=%s score=%s reasons=%s", event.event_id, event.vehicle_id, result.score, result.reasons)
    db.commit()
    metrics["events_processed"] += 1
    return {"status": "processed", "score": result.score, "severity": result.severity, "reasons": result.reasons}
