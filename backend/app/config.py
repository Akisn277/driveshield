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
KAFKA_CONSUMER_WORKERS = int(os.getenv("KAFKA_CONSUMER_WORKERS", str(KAFKA_PARTITIONS)))
KAFKA_CONSUMER_BATCH_SIZE = int(os.getenv("KAFKA_CONSUMER_BATCH_SIZE", "2000"))
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "fleet_manager")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "change-me-now")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-this-secret")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))