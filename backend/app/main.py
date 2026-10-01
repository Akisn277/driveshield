import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.ingest import router as ingest_router
from app.api.vehicles import router as vehicles_router
from app.database.postgres import Base, engine
from app.services.kafka_consumer import consumer_loop
from app.services.telemetry_service import metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(consumer_loop())
    yield
    task.cancel()


app = FastAPI(
    title="DriveShield API",
    description="Real-time connected vehicle anomaly detection platform",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(alerts_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(ingest_router)
app.include_router(vehicles_router)


@app.get("/")
def root():
    return {
        "service": "DriveShield API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "events_processed": metrics["events_processed"],
        "events_rejected": metrics["events_rejected"],
        "duplicates": metrics["duplicates"],
        "database_failures": metrics["database_failures"],
        "batches_processed": metrics["batches_processed"],
    }