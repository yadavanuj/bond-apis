from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from ..models import TypeRegistry, TypeRegistryCreate, TypeRegistryUpdate
from ..database import get_database
from ..cache import RegistryCache
from datetime import datetime

router = APIRouter()

@router.post("/types", response_model=TypeRegistry)
async def create_type(type_registry: TypeRegistryCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    type_dict = type_registry.model_dump()
    
    if type_registry.sensitivity not in RegistryCache.sensitivities:
        raise HTTPException(status_code=400, detail=f"Invalid sensitivity: {type_registry.sensitivity}")

    # Check if type_id already exists
    existing_type = await db.type_registry.find_one({"type_id": type_dict["type_id"]})
    if existing_type:
        raise HTTPException(status_code=400, detail="Type ID already exists")
    
    type_dict["created_at"] = datetime.utcnow()
    type_dict["updated_at"] = datetime.utcnow()
    result = await db.type_registry.insert_one(type_dict)
    type_dict["_id"] = result.inserted_id
    return TypeRegistry(**type_dict)

@router.get("/types", response_model=List[TypeRegistry])
async def get_types(db: AsyncIOMotorDatabase = Depends(get_database)):
    types = []
    async for type_doc in db.type_registry.find():
        types.append(TypeRegistry(**type_doc))
    return types

@router.get("/types/{type_id}", response_model=TypeRegistry)
async def get_type(type_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    type_doc = await db.type_registry.find_one({"type_id": type_id})
    if not type_doc:
        raise HTTPException(status_code=404, detail="Type not found")
    return TypeRegistry(**type_doc)

@router.put("/types/{type_id}", response_model=TypeRegistry)
async def update_type(type_id: str, type_update: TypeRegistryUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = {k: v for k, v in type_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    if type_update.sensitivity and type_update.sensitivity not in RegistryCache.sensitivities:
        raise HTTPException(status_code=400, detail=f"Invalid sensitivity: {type_update.sensitivity}")

    update_data["updated_at"] = datetime.utcnow()
    update_data.pop("version", None)

    result = await db.type_registry.update_one({"type_id": type_id}, {"$set": update_data, "$inc": {"version": 1}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Type not found")
    
    updated_type = await db.type_registry.find_one({"type_id": type_id})
    return TypeRegistry(**updated_type)

@router.delete("/types/{type_id}")
async def delete_type(type_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.type_registry.delete_one({"type_id": type_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Type not found")
    return {"message": "Type deleted successfully"}
