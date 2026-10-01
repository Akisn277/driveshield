from dataclasses import dataclass
from math import cos, radians, sqrt
from typing import Any


@dataclass
class DetectionResult:
    score: int
    severity: str
    reasons: list[str]


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat_scale = 111.0
    lon_scale = 111.0 * cos(radians((lat1 + lat2) / 2))
    return sqrt(((lat2 - lat1) * lat_scale) ** 2 + ((lon2 - lon1) * lon_scale) ** 2)


def severity_for_score(score: int) -> str:
    if score <= 30:
        return "NORMAL"
    if score <= 60:
        return "MEDIUM"
    if score <= 80:
        return "HIGH"
    return "CRITICAL"


def detect_anomalies(event: Any, vehicle: Any) -> DetectionResult:
    score = 0
    reasons: list[str] = []

    if event.speed > vehicle.max_speed:
        score += 30
        reasons.append("Overspeed")
    if event.temperature > vehicle.normal_temperature_max:
        score += 25
        reasons.append("High temperature")
    elif event.temperature < vehicle.normal_temperature_min:
        score += 20
        reasons.append("Abnormally low temperature")
    hour = event.timestamp.hour
    if event.ignition and not vehicle.normal_operating_start <= hour <= vehicle.normal_operating_end:
        score += 15
        reasons.append("Unusual operating time")
    if _distance_km(vehicle.latitude, vehicle.longitude, event.latitude, event.longitude) > vehicle.allowed_radius_km:
        score += 20
        reasons.append("Location deviation")

    score = min(score, 100)
    return DetectionResult(score, severity_for_score(score), reasons)
