from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from datetime import datetime, timezone

from app.database.postgres import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String(64), unique=True, nullable=False, index=True)
    vehicle_type = Column(String(64), default="fleet")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    max_speed = Column(Float, default=100)
    speed = Column(Float, default=0)
    temperature = Column(Float, default=0)
    battery = Column(Float, default=0)
    fuel_level = Column(Float, default=0)
    ignition = Column(Boolean, default=False)
    normal_temperature_min = Column(Float, default=60)
    normal_temperature_max = Column(Float, default=95)
    normal_operating_start = Column(Integer, default=6)
    normal_operating_end = Column(Integer, default=22)
    allowed_radius_km = Column(Float, default=5)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))