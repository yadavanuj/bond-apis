from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from ..models import Policy, PolicyCreate, PolicyUpdate
from ..database import get_database
from datetime import datetime

router = APIRouter()

@router.post("/policies", response_model=Policy)
async def create_policy(policy: PolicyCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    policy_dict = policy.model_dump()
    policy_dict["created_at"] = datetime.utcnow()
    policy_dict["updated_at"] = datetime.utcnow()
    result = await db.policies.insert_one(policy_dict)
    policy_dict["_id"] = result.inserted_id
    return Policy(**policy_dict)

@router.get("/policies", response_model=List[Policy])
async def get_policies(db: AsyncIOMotorDatabase = Depends(get_database)):
    policies = []
    async for policy in db.policies.find():
        policies.append(Policy(**policy))
    return policies

@router.get("/policies/{policy_id}", response_model=Policy)
async def get_policy(policy_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    policy = await db.policies.find_one({"policy_id": policy_id})
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return Policy(**policy)

@router.put("/policies/{policy_id}", response_model=Policy)
async def update_policy(policy_id: str, policy_update: PolicyUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = {k: v for k, v in policy_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.utcnow()
    update_data.pop("version", None)

    result = await db.policies.update_one({"policy_id": policy_id}, {"$set": update_data, "$inc": {"version": 1}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    updated_policy = await db.policies.find_one({"policy_id": policy_id})
    return Policy(**updated_policy)

@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.policies.delete_one({"policy_id": policy_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"message": "Policy deleted successfully"}
