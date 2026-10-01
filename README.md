# DriveShield

DriveShield is a small end-to-end connected-vehicle intelligence demo. A simulator publishes validated telemetry to Kafka; one FastAPI application consumes it, stores raw telemetry in MongoDB, evaluates explainable deterministic rules, and stores vehicles, anomaly events, and alerts in PostgreSQL. A Next.js dashboard polls the API for operations views.

## Architecture

`simulator -> Kafka vehicle-telemetry -> FastAPI consumer -> MongoDB + PostgreSQL -> Next.js dashboard`

The backend is deliberately one application. Kafka is configured with a host listener at `localhost:9092` and a container listener at `kafka:9093`.

## Stack

FastAPI, SQLAlchemy, PostgreSQL, MongoDB, Apache Kafka, confluent-kafka, Next.js, TypeScript, Tailwind CSS, and k6.

## Run with Docker Compose

From PowerShell or Windows CMD:

```text
docker compose up --build
```

Open the dashboard at http://localhost:3000, Swagger at http://localhost:8000/docs, the API at http://localhost:8000, and Kafka UI at http://localhost:8080.

The dashboard requires fleet-manager login. Set `AUTH_USERNAME`, `AUTH_PASSWORD`, and `JWT_SECRET_KEY` in your local `.env` before starting Compose; the fallback values are for development only. The login endpoint is `POST /api/auth/login`.

## Run locally

Start infrastructure first with `docker compose up postgres mongodb kafka kafka-ui`. In a second PowerShell window:

```text
cd backend
venv\Scripts\activate
pip install -r requirements.txt
$env:POSTGRES_URL="postgresql://driveshield:driveshield123@localhost:5432/driveshield"
$env:MONGO_URL="mongodb://localhost:27017"
$env:KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
uvicorn app.main:app --reload --port 8000
```

In another window:

```text
cd simulator
python -m pip install -r requirements.txt
python vehicle_simulator.py --vehicles 1000 --rate 10
```

For a quick recording-friendly stream, use `python vehicle_simulator.py --demo --rate 2`. The demo produces `VH-DEMO-001`, `VH-DEMO-002`, and `VH-DEMO-003` with obvious anomalies. The large mode is `python vehicle_simulator.py --vehicles 100000 --rate 1000`; it generates events incrementally and does not retain all vehicles in memory.

## API

- `POST /api/auth/login` returns a Bearer JWT for the configured fleet manager.
- `GET /` and `GET /health`
- `GET /api/dashboard/summary`
- `GET /api/alerts?severity=HIGH&anomaly_type=Overspeed&page=1&page_size=25`
- `GET /api/alerts/recent`
- `GET /api/vehicles`
- `GET /api/vehicles/{vehicle_id}`
- `GET /api/analytics/anomalies`

PostgreSQL tables are created automatically on startup. MongoDB database `driveshield`, collection `telemetry`, stores raw events.

## Detection rules

Overspeed adds 30, high temperature 25, low temperature 20, unusual operating time 15, and location deviation outside the vehicle's five-kilometre reference radius 20. Scores are capped at 100. Severity is NORMAL 0-30, MEDIUM 31-60, HIGH 61-80, and CRITICAL 81-100. Every alert stores its human-readable reasons.

## Tests and load testing

```text
$env:PYTHONPATH="backend"
backend\venv\Scripts\python.exe -m pytest tests -q
```

The k6 script posts representative events to the optional HTTP ingestion endpoint when available. The current MVP's production path is Kafka, so for throughput demonstrations prefer the simulator. A laptop benchmark is illustrative only and is not a claim of 100,000 events per second.

## Known limitations and future improvements

The MVP uses an in-memory duplicate cache, creates profiles on first observation, uses local fleet-manager JWT authentication, and uses polling rather than WebSockets. Future work can add durable idempotency, retry/dead-letter handling, richer geofences, external identity providers, retention policies, charts, and measured load-test reports. No performance number should be inferred without measuring the target environment.
