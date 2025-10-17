# stir-backend/app/db/mongodb.py

import motor.motor_asyncio
from core.config import settings

# The MongoDB client is created once and shared
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)

# get_default_database() will use the database specified in your MONGO_URI
db = client.get_default_database()