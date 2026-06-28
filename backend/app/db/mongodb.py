from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import os

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db = MongoDB()

def _build_mongo_url() -> str:
    """Build MongoDB URL with URL-encoded credentials to handle special chars like @ and !"""
    user = os.getenv("MONGO_USER", "")
    password = os.getenv("MONGO_PASSWORD", "")
    host = "aegis-mongodb"
    port = "27017"

    if user and password:
        encoded_pw = quote_plus(password)
        return f"mongodb://{user}:{encoded_pw}@{host}:{port}"
    # Fallback: use the raw URL as-is (for unauthenticated dev setups)
    return settings.MONGODB_URL

async def connect_to_mongo():
    mongo_url = _build_mongo_url()
    db.client = AsyncIOMotorClient(mongo_url)
    db.db = db.client[settings.MONGODB_DB]

async def close_mongo_connection():
    if db.client:
        db.client.close()
