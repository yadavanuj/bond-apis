from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """Connect to MongoDB"""
    try:
        db.client = AsyncIOMotorClient(MONGO_URI, tz_aware=True)
        db.database = db.client[MONGO_DB_NAME]
        # Test the connection
        await db.client.admin.command('ping')
        print("Connected to MongoDB")
    except ConnectionFailure:
        print("Failed to connect to MongoDB")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")

def get_database():
    """Get database instance"""
    return db.database

async def create_collection_indexes():
    """
    Enforce uniqueness constraints at the database level.
    This prevents duplicate IDs and ensures data integrity.
    """
    if db.database is None:
        return

    constraints = [
        ("tenants", "tenant_id"),
        ("projects", "project_id"),
        ("workflows", "workflow_id"),
        ("data_models", "model_id"),
        ("relationships", "relationship_id"),
        ("policies", "policy_id"),
        ("type_registry", "type_id"),
        ("sensitivity_registry", "sensitivity_id"),
        ("action_registry", "action_id"),
        ("operator_registry", "operator_id"),
        ("charset_registry", "charset_id"),
    ]

    for col_name, field in constraints:
        try:
            # Create unique index to prevent duplicates
            await db.database[col_name].create_index(field, unique=True)
            print(f"Ensured unique index on {col_name}.{field}")
        except (DuplicateKeyError, OperationFailure) as e:
            print(f"⚠️ Failed to create unique index on {col_name}.{field}: {e}")
            print(f"   ↳ HINT: Run 'python -m src.cleanup' to remove duplicate/invalid records.")
