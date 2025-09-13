from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

# Global database instance
db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db.database = db.client[settings.DATABASE_NAME]
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB!")
        
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")

async def get_database():
    """Get database instance"""
    return db.database

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        database = await get_database()
        collection = database["audio_files"]
        
        # Create index on language field for faster queries
        await collection.create_index("language")
        
        # Create index on created_at for sorting
        await collection.create_index("created_at")
        
        # Create compound index for language and created_at
        await collection.create_index([("language", 1), ("created_at", -1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        raise e
