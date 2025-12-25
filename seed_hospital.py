import asyncio
import sys
import os

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import connect_to_mongo, close_mongo_connection, get_database
from src.seeding import seed_hospital_data
from src.seeding_generic import seed_generic_data

async def main():
    print("🚀 Initializing Bond Platform Bootstrap...")
    
    try:
        await connect_to_mongo()
        db = get_database()
        
        # Run the generic seeding first (Registries, Common Types)
        await seed_generic_data(db)
        
        # Run the hospital domain seeding
        await seed_hospital_data(db)
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
    finally:
        await close_mongo_connection()
        print("👋 Bootstrap finished.")

if __name__ == "__main__":
    asyncio.run(main())