import argparse
import json
import logging
import random
import time
from datetime import timedelta
from datetime import datetime, timezone

from anomaly_injector import choose, inject
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def vehicle_id(index: int, demo: bool) -> str:
    if demo and index < 3:
        return f"VH-DEMO-{index + 1:03d}"
    return f"VH-{index + 1:06d}"


def make_event(index: int, demo: bool, sequence: int, anomaly_probability: float) -> dict:
    latitude, longitude = 12.8458 + random.uniform(-0.02, 0.02), 80.0165 + random.uniform(-0.02, 0.02)
    event = {"event_id": f"evt_{sequence:09d}", "vehicle_id": vehicle_id(index, demo), "timestamp": datetime.now(timezone.utc).isoformat(), "latitude": latitude, "longitude": longitude, "speed": max(0, random.gauss(55, 12)), "temperature": random.gauss(75, 3), "battery": random.uniform(65, 95), "fuel_level": random.uniform(35, 90), "ignition": True}
    kind = ["combined", "overspeed", "location_deviation"][index] if demo and index < 3 else choose(anomaly_probability)
    return inject(event, kind) if kind else event


def main() -> None:
    parser = argparse.ArgumentParser(description="DriveShield streaming vehicle simulator")
    parser.add_argument("--vehicles", type=int, default=1000)
    parser.add_argument("--rate", type=float, default=10, help="events per second; zero means unthrottled")
    parser.add_argument("--anomaly-probability", type=float, default=0.01)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.vehicles < 1:
        parser.error("--vehicles must be positive")
    try:
        from confluent_kafka import Producer
    except ImportError as exc:
        raise SystemExit("Install simulator requirements first: pip install -r requirements.txt") from exc
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS, "queue.buffering.max.messages": 100000})
    sequence = 0
    index = 0
    previous_payload = None
    logging.info("publishing vehicles=%s rate=%s topic=%s", args.vehicles, args.rate, KAFKA_TOPIC)
    try:
        while True:
            event = make_event(index, args.demo, sequence, args.anomaly_probability)
            if sequence and sequence % 113 == 0 and previous_payload is not None:
                producer.produce(KAFKA_TOPIC, key=event["vehicle_id"], value=previous_payload)
                logging.info("published deliberate duplicate sequence=%s", sequence)
            if sequence and sequence % 127 == 0:
                event["timestamp"] = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
            payload = json.dumps(event).encode("utf-8")
            producer.produce(KAFKA_TOPIC, key=event["vehicle_id"], value=payload)
            previous_payload = payload
            sequence += 1
            index = (index + 1) % args.vehicles
            if sequence % 100 == 0:
                producer.flush(1)
                logging.info("published events=%s", sequence)
            if args.rate > 0:
                time.sleep(1 / args.rate)
    except KeyboardInterrupt:
        logging.info("stopping simulator")
    finally:
        producer.flush(10)


if __name__ == "__main__":
    main()
