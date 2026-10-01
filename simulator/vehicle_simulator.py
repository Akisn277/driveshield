import argparse
import json
import logging
import random
import time
from datetime import timedelta
from datetime import datetime, timezone
from pathlib import Path

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


def producer_config() -> dict:
    return {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "queue.buffering.max.messages": 500000,
        "queue.buffering.max.kbytes": 1048576,
        "linger.ms": 5,
        "batch.num.messages": 10000,
        "compression.type": "lz4",
    }


def padded_payload(event: dict, target_bytes: int) -> bytes:
    payload = json.dumps(event, separators=(",", ":")).encode("utf-8")
    return payload + b" " * max(0, target_bytes - len(payload))


def read_backend_health(backend_url: str) -> dict:
    from urllib.request import urlopen

    try:
        with urlopen(f"{backend_url.rstrip('/')}/health", timeout=5) as response:
            return json.loads(response.read())
    except Exception as exc:
        logging.warning("backend health unavailable error=%s", exc)
        return {}


def consumer_group_lag(Consumer) -> int | None:
    try:
        observer = Consumer({
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "driveshield-benchmark-observer",
            "enable.auto.commit": False,
        })
        metadata = observer.list_topics(KAFKA_TOPIC, timeout=5)
        partition_ids = list(metadata.topics[KAFKA_TOPIC].partitions)
        topic_partitions = [__import__("confluent_kafka").TopicPartition(KAFKA_TOPIC, partition_id) for partition_id in partition_ids]
        committed = observer.committed(topic_partitions, timeout=5)
        lag = 0
        for partition in committed:
            _, high = observer.get_watermark_offsets(partition, timeout=5)
            if partition.offset < 0:
                lag += high
            else:
                lag += max(0, high - partition.offset)
        observer.close()
        return lag
    except Exception as exc:
        logging.warning("Kafka lag unavailable error=%s", exc)
        return None


def run_benchmark(args, Producer, Consumer) -> None:
    stats = {"attempted": 0, "published": 0, "publish_errors": 0, "duplicates": 0, "out_of_order": 0}

    def delivery_callback(error, _message):
        if error:
            stats["publish_errors"] += 1
        else:
            stats["published"] += 1

    before = read_backend_health(args.backend_url)
    producer = Producer(producer_config())
    start = time.perf_counter()
    deadline = start + args.duration
    sequence = 0
    index = 0
    previous_payload = None
    event_prefix = f"bench_{int(time.time())}"
    while time.perf_counter() < deadline:
        elapsed = time.perf_counter() - start
        allowed = int(args.events_per_second * elapsed) + 1
        if stats["attempted"] >= allowed:
            producer.poll(0.001)
            continue
        event = make_event(index, args.demo, sequence, args.anomaly_probability)
        event["event_id"] = f"{event_prefix}_{sequence:09d}"
        if sequence and sequence % 113 == 0 and previous_payload is not None:
            payload = previous_payload
            stats["duplicates"] += 1
        else:
            if sequence and sequence % 127 == 0:
                event["timestamp"] = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
                stats["out_of_order"] += 1
            payload = padded_payload(event, args.payload_bytes)
            previous_payload = payload
        try:
            producer.produce(KAFKA_TOPIC, key=event["vehicle_id"], value=payload, on_delivery=delivery_callback)
            stats["attempted"] += 1
        except BufferError:
            stats["publish_errors"] += 1
            producer.poll(0.01)
            continue
        producer.poll(0)
        sequence += 1
        index = (index + 1) % args.vehicles
    undelivered = producer.flush(10)
    stats["publish_errors"] += undelivered
    elapsed = time.perf_counter() - start
    after = read_backend_health(args.backend_url)
    lag = consumer_group_lag(Consumer)
    processed = max(0, after.get("events_processed", 0) - before.get("events_processed", 0))
    report = {
        "target_rate": args.events_per_second,
        "duration_seconds": round(elapsed, 2),
        "target_events": args.events_per_second * args.duration,
        "attempted": stats["attempted"],
        "published": stats["published"],
        "consumed_processed": processed,
        "actual_publish_rate": round(stats["published"] / elapsed, 2),
        "actual_consume_rate": round(processed / elapsed, 2),
        "publish_errors": stats["publish_errors"],
        "consumer_rejected_delta": after.get("events_rejected", 0) - before.get("events_rejected", 0),
        "duplicate_events": stats["duplicates"] + after.get("duplicates", 0) - before.get("duplicates", 0),
        "database_failure_delta": after.get("database_failures", 0) - before.get("database_failures", 0),
        "kafka_lag": lag,
        "payload_bytes": args.payload_bytes,
        "partitions": 6,
    }
    report_json = json.dumps(report, indent=2)
    print(report_json)
    if args.report_file:
        Path(args.report_file).write_text(report_json, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="DriveShield streaming vehicle simulator")
    parser.add_argument("--vehicles", type=int, default=1000)
    parser.add_argument("--rate", type=float, default=10, help="events per second; zero means unthrottled")
    parser.add_argument("--events-per-second", type=int)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--payload-bytes", type=int, default=1024)
    parser.add_argument("--backend-url", default="http://localhost:8000")
    parser.add_argument("--report-file")
    parser.add_argument("--anomaly-probability", type=float, default=0.01)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.vehicles < 1:
        parser.error("--vehicles must be positive")
    try:
        from confluent_kafka import Consumer, Producer
    except ImportError as exc:
        raise SystemExit("Install simulator requirements first: pip install -r requirements.txt") from exc
    if args.events_per_second is not None:
        if args.events_per_second < 1 or args.duration < 1:
            parser.error("--events-per-second and --duration must be positive")
        run_benchmark(args, Producer, Consumer)
        return
    producer = Producer(producer_config())
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
            if sequence % 1000 == 0:
                producer.poll(0)
                logging.info("published events=%s", sequence)
            if args.rate > 0:
                time.sleep(1 / args.rate)
    except KeyboardInterrupt:
        logging.info("stopping simulator")
    finally:
        producer.flush(10)


if __name__ == "__main__":
    main()
