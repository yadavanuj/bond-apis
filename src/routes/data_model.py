from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from ..models import DataModel, DataModelCreate, DataModelUpdate
from ..database import get_database

router = APIRouter()

@router.post("/data_models", response_model=DataModel)
async def create_data_model(data_model: DataModelCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    data_model_dict = data_model.model_dump()
    result = await db.data_models.insert_one(data_model_dict)
    data_model_dict["_id"] = result.inserted_id
    return DataModel(**data_model_dict)

@router.get("/data_models", response_model=List[DataModel])
async def get_data_models(db: AsyncIOMotorDatabase = Depends(get_database)):
    data_models = []
    async for data_model in db.data_models.find():
        data_models.append(DataModel(**data_model))
    return data_models

@router.get("/data_models/{model_id}", response_model=DataModel)
async def get_data_model(model_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    data_model = await db.data_models.find_one({"model_id": model_id})
    if not data_model:
        raise HTTPException(status_code=404, detail="Data model not found")
    return DataModel(**data_model)

@router.put("/data_models/{model_id}", response_model=DataModel)
async def update_data_model(model_id: str, data_model_update: DataModelUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = {k: v for k, v in data_model_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.data_models.update_one({"model_id": model_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Data model not found")
    updated_data_model = await db.data_models.find_one({"model_id": model_id})
    return DataModel(**updated_data_model)

@router.delete("/data_models/{model_id}")
async def delete_data_model(model_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.data_models.delete_one({"model_id": model_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Data model not found")
    return {"message": "Data model deleted successfully"}
