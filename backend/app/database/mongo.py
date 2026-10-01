from pymongo import MongoClient

from app.config import MONGO_DB, MONGO_URL

_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=2000)
database = _client[MONGO_DB]
telemetry_collection = database["telemetry"]
