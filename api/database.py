import os
from pymongo import MongoClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "market_data")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "binance_trades")

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DATABASE]
trades_collection = db[MONGODB_COLLECTION]
