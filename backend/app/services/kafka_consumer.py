import asyncio
import json
import logging
import time

from app.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_CONSUMER_BATCH_SIZE, KAFKA_CONSUMER_WORKERS, KAFKA_PARTITIONS, KAFKA_TELEMETRY_TOPIC
from app.database.postgres import SessionLocal
from app.schemas.telemetry import TelemetryEvent
from app.services.telemetry_service import metrics, process_events

logger = logging.getLogger("driveshield")


def _consume_batch(consumer, batch_size: int, max_wait: float = 0.25):
    messages = []
    deadline = time.monotonic() + max_wait
    while len(messages) < batch_size:
        remaining = deadline - time.monotonic()
        if remaining <= 0 and messages:
            break
        chunk = consumer.consume(
            num_messages=batch_size - len(messages),
            timeout=max(0.01, min(0.05, remaining)) if remaining > 0 else 0.01,
        )
        if not chunk:
            break
        messages.extend(chunk)
    return messages


def _process_messages(payloads: list[bytes]):
    db = SessionLocal()
    try:
        events = []
        for payload in payloads:
            try:
                events.append(TelemetryEvent.model_validate(json.loads(payload)))
            except Exception as exc:
                metrics["events_rejected"] += 1
                logger.warning("event rejected error=%s", exc)
        if events:
            process_events(events, db)
    finally:
        db.close()


async def _consumer_worker(Consumer, worker_id: int):
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "driveshield-backend",
        "client.id": f"driveshield-backend-{worker_id}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "fetch.min.bytes": 1048576,
        "fetch.wait.max.ms": 50,
        "queued.min.messages": 10000,
        "max.partition.fetch.bytes": 10485760,
        "max.poll.interval.ms": 300000,
    })
    consumer.subscribe([KAFKA_TELEMETRY_TOPIC])
    logger.info("Kafka consumer worker=%s subscribed topic=%s partitions=%s", worker_id, KAFKA_TELEMETRY_TOPIC, KAFKA_PARTITIONS)
    try:
        while True:
            messages = await asyncio.to_thread(_consume_batch, consumer, KAFKA_CONSUMER_BATCH_SIZE)
            if not messages:
                await asyncio.sleep(0)
                continue
            valid_messages = [message for message in messages if not message.error()]
            metrics["events_rejected"] += len(messages) - len(valid_messages)
            if valid_messages:
                try:
                    await asyncio.to_thread(_process_messages, [message.value() for message in valid_messages])
                except Exception as exc:
                    metrics["events_rejected"] += len(valid_messages)
                    logger.exception("batch processing error worker=%s size=%s error=%s", worker_id, len(valid_messages), exc)
    except asyncio.CancelledError:
        consumer.close()
        raise


async def consumer_loop():
    try:
        from confluent_kafka import Consumer
    except ImportError:
        logger.warning("confluent-kafka is unavailable; Kafka consumer is disabled")
        while True:
            await asyncio.sleep(60)
    workers = max(1, min(KAFKA_CONSUMER_WORKERS, KAFKA_PARTITIONS))
    await asyncio.gather(*(_consumer_worker(Consumer, worker_id) for worker_id in range(workers)))
