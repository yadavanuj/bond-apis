from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from ..models import Relationship, RelationshipCreate, RelationshipUpdate
from ..database import get_database
from datetime import datetime

router = APIRouter()

@router.post("/relationships", response_model=Relationship)
async def create_relationship(relationship: RelationshipCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    relationship_dict = relationship.model_dump()
    relationship_dict["created_at"] = datetime.utcnow()
    relationship_dict["updated_at"] = datetime.utcnow()
    result = await db.relationships.insert_one(relationship_dict)
    relationship_dict["_id"] = result.inserted_id
    return Relationship(**relationship_dict)

@router.get("/relationships", response_model=List[Relationship])
async def get_relationships(db: AsyncIOMotorDatabase = Depends(get_database)):
    relationships = []
    async for relationship in db.relationships.find():
        relationships.append(Relationship(**relationship))
    return relationships

@router.get("/relationships/{relationship_id}", response_model=Relationship)
async def get_relationship(relationship_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    relationship = await db.relationships.find_one({"relationship_id": relationship_id})
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return Relationship(**relationship)

@router.put("/relationships/{relationship_id}", response_model=Relationship)
async def update_relationship(relationship_id: str, relationship_update: RelationshipUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = {k: v for k, v in relationship_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.utcnow()
    result = await db.relationships.update_one({"relationship_id": relationship_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Relationship not found")
    updated_relationship = await db.relationships.find_one({"relationship_id": relationship_id})
    return Relationship(**updated_relationship)

@router.delete("/relationships/{relationship_id}")
async def delete_relationship(relationship_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.relationships.delete_one({"relationship_id": relationship_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return {"message": "Relationship deleted successfully"}