# utils/database.py
import os
import pymongo
from dotenv import load_dotenv

load_dotenv("config.env")

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise Exception("MONGO_URL not set in config.env")

client = pymongo.MongoClient(MONGO_URL)
db = client["MovieBotV2"]
movies = db["movies"]
counters = db["counters"]

# initialize counter doc if not exists
def _ensure_counter():
    cnt = counters.find_one({"_id": "code"})
    if not cnt:
        counters.insert_one({"_id": "code", "value": 0})

_ensure_counter()

def get_next_code():
    # increments and returns D-xxx format
    res = counters.find_one_and_update(
        {"_id": "code"},
        {"$inc": {"value": 1}},
        return_document=pymongo.ReturnDocument.AFTER
    )
    num = res["value"]
    return f"D-{num:03d}"

def save_movie(code: str, data: dict):
    """Upsert movie data keyed by code"""
    movies.update_one({"code": code}, {"$set": data}, upsert=True)

def get_movie(code: str):
    return movies.find_one({"code": code})

def list_codes():
    return [m["code"] for m in movies.find({}, {"code": 1, "_id": 0})]

def delete_movie(code: str):
    movies.delete_one({"code": code})

def backup_all():
    return list(movies.find({}, {"_id": 0}))
  
