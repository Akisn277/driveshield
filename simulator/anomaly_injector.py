import random


def inject(event: dict, kind: str) -> dict:
    if kind in {"overspeed", "combined"}:
        event["speed"] = 150.0
    if kind in {"temperature_spike", "combined"}:
        event["temperature"] = 115.0
    if kind in {"location_deviation", "combined"}:
        event["latitude"] += 0.2
        event["longitude"] += 0.2
    if kind == "unusual_operating_time":
        event["ignition"] = True
    return event


def choose(probability: float) -> str | None:
    if random.random() >= probability:
        return None
    return random.choice(["overspeed", "temperature_spike", "location_deviation", "unusual_operating_time", "combined"])
