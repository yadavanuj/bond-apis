from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from ..models import FieldModel, FieldCreate, FieldUpdate
from ..database import get_database

router = APIRouter()

@router.post("/fields", response_model=FieldModel)
async def create_field(field: FieldCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    field_dict = field.model_dump()
    result = await db.fields.insert_one(field_dict)
    field_dict["_id"] = result.inserted_id
    return FieldModel(**field_dict)

@router.get("/fields", response_model=List[FieldModel])
async def get_fields(db: AsyncIOMotorDatabase = Depends(get_database)):
    fields = []
    async for field in db.fields.find():
        fields.append(FieldModel(**field))
    return fields

@router.get("/fields/{field_id}", response_model=FieldModel)
async def get_field(field_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    field = await db.fields.find_one({"field_id": field_id})
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return FieldModel(**field)

@router.put("/fields/{field_id}", response_model=FieldModel)
async def update_field(field_id: str, field_update: FieldUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = {k: v for k, v in field_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.fields.update_one({"field_id": field_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Field not found")
    updated_field = await db.fields.find_one({"field_id": field_id})
    return FieldModel(**updated_field)

@router.delete("/fields/{field_id}")
async def delete_field(field_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.fields.delete_one({"field_id": field_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Field not found")
    return {"message": "Field deleted successfully"}
