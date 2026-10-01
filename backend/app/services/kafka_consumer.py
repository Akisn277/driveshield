import asyncio
import json
import logging

from app.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_PARTITIONS, KAFKA_TELEMETRY_TOPIC
from app.database.postgres import SessionLocal
from app.schemas.telemetry import TelemetryEvent
from app.services.telemetry_service import metrics, process_event

logger = logging.getLogger("driveshield")


def _process_message(payload: bytes):
    db = SessionLocal()
    try:
        event = TelemetryEvent.model_validate(json.loads(payload))
        process_event(event, db)
    finally:
        db.close()


async def consumer_loop():
    try:
        from confluent_kafka import Consumer, KafkaException
    except ImportError:
        logger.warning("confluent-kafka is unavailable; Kafka consumer is disabled")
        while True:
            await asyncio.sleep(60)

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "driveshield-backend",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    consumer.subscribe([KAFKA_TELEMETRY_TOPIC])
    logger.info("Kafka consumer subscribed topic=%s partitions=%s", KAFKA_TELEMETRY_TOPIC, KAFKA_PARTITIONS)
    try:
        while True:
            message = consumer.poll(0.5)
            if message is None:
                await asyncio.sleep(0)
                continue
            if message.error():
                logger.error("Kafka processing error=%s", message.error())
                continue
            try:
                await asyncio.to_thread(_process_message, message.value())
            except Exception as exc:
                metrics["events_rejected"] += 1
                logger.exception("event rejected error=%s", exc)
    except asyncio.CancelledError:
        consumer.close()
        raise
