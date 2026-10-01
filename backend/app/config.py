import os


POSTGRES_URL = os.getenv(
	"POSTGRES_URL",
	"postgresql://driveshield:driveshield123@localhost:5432/driveshield",
)
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "driveshield")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TELEMETRY_TOPIC = os.getenv("KAFKA_TELEMETRY_TOPIC", "vehicle-telemetry")
KAFKA_PARTITIONS = int(os.getenv("KAFKA_PARTITIONS", "6"))