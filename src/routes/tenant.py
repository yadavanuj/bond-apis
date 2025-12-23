from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime
from ..models import Tenant, TenantCreate, TenantUpdate
from ..database import get_database

router = APIRouter()

@router.post("/tenants", response_model=Tenant)
async def create_tenant(tenant: TenantCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    tenant_dict = tenant.model_dump()
    tenant_dict["created_at"] = datetime.utcnow()
    result = await db.tenants.insert_one(tenant_dict)
    tenant_dict["_id"] = result.inserted_id
    return Tenant(**tenant_dict)

@router.get("/tenants", response_model=List[Tenant])
async def get_tenants(db: AsyncIOMotorDatabase = Depends(get_database)):
    tenants = []
    async for tenant in db.tenants.find():
        tenants.append(Tenant(**tenant))
    return tenants

@router.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    tenant = await db.tenants.find_one({"tenant_id": tenant_id})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return Tenant(**tenant)

@router.put("/tenants/{tenant_id}", response_model=Tenant)
async def update_tenant(tenant_id: str, tenant_update: TenantUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = {k: v for k, v in tenant_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.tenants.update_one({"tenant_id": tenant_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    updated_tenant = await db.tenants.find_one({"tenant_id": tenant_id})
    return Tenant(**updated_tenant)

@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.tenants.delete_one({"tenant_id": tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": "Tenant deleted successfully"}
