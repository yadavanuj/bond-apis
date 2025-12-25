from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..seeding import seed_hospital_data

router = APIRouter()

@router.post("/seed/hospital")
async def seed_hospital(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Trigger the hospital chatbot onboarding seed process."""
    return await seed_hospital_data(db)