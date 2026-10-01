from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.anomaly_detector import detect_anomalies, severity_for_score
from app.schemas.telemetry import TelemetryEvent


def vehicle(**overrides):
    values = dict(latitude=12.8458, longitude=80.0165, max_speed=90, normal_temperature_min=60, normal_temperature_max=95, normal_operating_start=6, normal_operating_end=22, allowed_radius_km=5)
    values.update(overrides)
    return SimpleNamespace(**values)


def event(**overrides):
    values = dict(event_id="evt-1", vehicle_id="VH-1", timestamp=datetime(2026, 10, 1, 12, tzinfo=timezone.utc), latitude=12.8458, longitude=80.0165, speed=50, temperature=75, battery=80, fuel_level=50, ignition=True)
    values.update(overrides)
    return TelemetryEvent(**values)


def test_normal_event():
    result = detect_anomalies(event(), vehicle())
    assert result.score == 0 and result.severity == "NORMAL" and result.reasons == []


def test_overspeed_and_temperature():
    result = detect_anomalies(event(speed=120, temperature=110), vehicle())
    assert result.score == 55
    assert result.reasons == ["Overspeed", "High temperature"]


def test_location_deviation():
    result = detect_anomalies(event(latitude=13.0, longitude=80.2), vehicle())
    assert "Location deviation" in result.reasons


def test_multiple_anomalies_are_capped():
    result = detect_anomalies(event(speed=200, temperature=110, latitude=13.0, longitude=80.2, timestamp=datetime(2026, 10, 1, 2, tzinfo=timezone.utc)), vehicle())
    assert result.score <= 100
    assert result.severity == "CRITICAL"


def test_severity_boundaries():
    assert severity_for_score(30) == "NORMAL"
    assert severity_for_score(31) == "MEDIUM"
    assert severity_for_score(61) == "HIGH"
    assert severity_for_score(81) == "CRITICAL"
