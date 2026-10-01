import json
import logging
from collections import deque
from threading import Lock
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.mongo import telemetry_collection
from app.models.alert import Alert
from app.models.anomaly_event import AnomalyEvent
from app.models.vehicle import Vehicle
from app.schemas.telemetry import TelemetryEvent
from app.services.anomaly_detector import detect_anomalies

logger = logging.getLogger("driveshield")
processed_event_ids: set[str] = set()
processed_event_order = deque()
processed_event_ids_lock = Lock()
MAX_PROCESSED_EVENT_IDS = 1_000_000
metrics = {"events_processed": 0, "events_rejected": 0, "duplicates": 0, "active_anomalies": 0, "database_failures": 0, "batches_processed": 0}


def process_event(event: TelemetryEvent, db: Session) -> dict:
    result = process_events([event], db)[0]
    return result


def process_events(events: list[TelemetryEvent], db: Session) -> list[dict]:
    unique_events = []
    for event in events:
        with processed_event_ids_lock:
            if event.event_id in processed_event_ids:
                metrics["duplicates"] += 1
                continue
            processed_event_ids.add(event.event_id)
            processed_event_order.append(event.event_id)
            if len(processed_event_order) > MAX_PROCESSED_EVENT_IDS:
                processed_event_ids.discard(processed_event_order.popleft())
        unique_events.append(event)

    if not unique_events:
        return [{"status": "duplicate", "event_id": event.event_id} for event in events]

    try:
        telemetry_collection.insert_many(
            [event.model_dump(mode="json") for event in unique_events],
            ordered=False,
        )
    except Exception as exc:
        metrics["database_failures"] += 1
        logger.warning("telemetry batch storage error size=%s error=%s", len(unique_events), exc)

    vehicle_ids = {event.vehicle_id for event in unique_events}
    rows = db.execute(
        select(
            Vehicle.id,
            Vehicle.vehicle_id,
            Vehicle.latitude,
            Vehicle.longitude,
            Vehicle.max_speed,
            Vehicle.normal_temperature_min,
            Vehicle.normal_temperature_max,
            Vehicle.normal_operating_start,
            Vehicle.normal_operating_end,
            Vehicle.allowed_radius_km,
        ).where(Vehicle.vehicle_id.in_(vehicle_ids))
    ).all()
    profiles = {
        row.vehicle_id: (row.id, SimpleNamespace(
            latitude=row.latitude,
            longitude=row.longitude,
            max_speed=row.max_speed,
            normal_temperature_min=row.normal_temperature_min,
            normal_temperature_max=row.normal_temperature_max,
            normal_operating_start=row.normal_operating_start,
            normal_operating_end=row.normal_operating_end,
            allowed_radius_km=row.allowed_radius_km,
        ))
        for row in rows
    }
    first_events = {}
    for event in unique_events:
        first_events.setdefault(event.vehicle_id, event)
    for vehicle_id in vehicle_ids - profiles.keys():
        event = first_events[vehicle_id]
        profiles[vehicle_id] = (None, SimpleNamespace(
            latitude=event.latitude,
            longitude=event.longitude,
            max_speed=100,
            normal_temperature_min=60,
            normal_temperature_max=95,
            normal_operating_start=6,
            normal_operating_end=22,
            allowed_radius_km=5,
        ))

    vehicle_inserts = []
    latest_vehicle_updates = {}

    results = []
    anomaly_rows = []
    alert_rows = []
    for event in unique_events:
        vehicle_row_id, vehicle = profiles[event.vehicle_id]
        result = detect_anomalies(event, vehicle)
        vehicle.latitude = event.latitude
        vehicle.longitude = event.longitude
        vehicle.speed = event.speed
        vehicle.temperature = event.temperature
        vehicle.battery = event.battery
        vehicle.fuel_level = event.fuel_level
        vehicle.ignition = event.ignition
        vehicle_values = {
            "latitude": event.latitude,
            "longitude": event.longitude,
            "speed": event.speed,
            "temperature": event.temperature,
            "battery": event.battery,
            "fuel_level": event.fuel_level,
            "ignition": event.ignition,
        }
        if vehicle_row_id is None:
            vehicle_inserts.append({
                "vehicle_id": event.vehicle_id,
                "vehicle_type": "fleet",
                "max_speed": vehicle.max_speed,
                "normal_temperature_min": vehicle.normal_temperature_min,
                "normal_temperature_max": vehicle.normal_temperature_max,
                "normal_operating_start": vehicle.normal_operating_start,
                "normal_operating_end": vehicle.normal_operating_end,
                "allowed_radius_km": vehicle.allowed_radius_km,
                "active": True,
                **vehicle_values,
            })
        else:
            latest_vehicle_updates[vehicle_row_id] = {"id": vehicle_row_id, **vehicle_values}
        results.append({"status": "processed", "score": result.score, "severity": result.severity, "reasons": result.reasons})
        if result.reasons:
            detected_at = event.timestamp.replace(tzinfo=None)
            anomaly_type = ", ".join(result.reasons)
            anomaly_rows.append({
                "event_id": event.event_id,
                "vehicle_id": event.vehicle_id,
                "anomaly_type": anomaly_type,
                "score": result.score,
                "severity": result.severity,
                "reasons": json.dumps(result.reasons),
                "detected_at": detected_at,
            })
            alert_rows.append({
                "alert_id": f"alert_{event.event_id}",
                "vehicle_id": event.vehicle_id,
                "anomaly_type": anomaly_type,
                "severity": result.severity,
                "score": result.score,
                "message": "; ".join(result.reasons),
                "detected_at": detected_at,
            })

    if vehicle_inserts:
        db.bulk_insert_mappings(Vehicle, vehicle_inserts)
    if latest_vehicle_updates:
        db.bulk_update_mappings(Vehicle, list(latest_vehicle_updates.values()))
    if anomaly_rows:
        db.bulk_insert_mappings(AnomalyEvent, anomaly_rows)
        db.bulk_insert_mappings(Alert, alert_rows)
        metrics["active_anomalies"] += len(anomaly_rows)
    try:
        db.commit()
    except Exception:
        metrics["database_failures"] += 1
        db.rollback()
        raise
    metrics["events_processed"] += len(unique_events)
    metrics["batches_processed"] += 1
    if anomaly_rows:
        logger.warning("anomalies detected batch_size=%s anomaly_count=%s", len(unique_events), len(anomaly_rows))
    return results
