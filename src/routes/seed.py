from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..database import get_database
from ..seeding import seed_hospital_data
from ..seeding_generic import seed_generic_data

router = APIRouter()

@router.post("/seed/generic")
async def seed_generic(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Trigger the generic/core data seeding process (Registries, Common Types)."""
    return await seed_generic_data(db)

@router.post("/seed/hospital")
async def seed_hospital(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Trigger the hospital chatbot onboarding seed process."""
    return await seed_hospital_data(db)