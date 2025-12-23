from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from ..models import SensitivityRegistry, ActionRegistry, OperatorRegistry, CharsetRegistry
from ..database import get_database
from ..cache import RegistryCache

router = APIRouter()

# Helper to create registry endpoints dynamically could be done, but explicit is clearer for now

# Sensitivity Registry
@router.post("/registries/sensitivities", response_model=SensitivityRegistry)
async def create_sensitivity(item: SensitivityRegistry, db: AsyncIOMotorDatabase = Depends(get_database)):
    if await db.sensitivity_registry.find_one({"sensitivity_id": item.sensitivity_id}):
        raise HTTPException(status_code=400, detail="ID already exists")
    await db.sensitivity_registry.insert_one(item.model_dump())
    RegistryCache.sensitivities.add(item.sensitivity_id)
    return item

@router.get("/registries/sensitivities", response_model=List[SensitivityRegistry])
async def get_sensitivities(db: AsyncIOMotorDatabase = Depends(get_database)):
    return [SensitivityRegistry(**doc) async for doc in db.sensitivity_registry.find()]

# Action Registry
@router.post("/registries/actions", response_model=ActionRegistry)
async def create_action(item: ActionRegistry, db: AsyncIOMotorDatabase = Depends(get_database)):
    if await db.action_registry.find_one({"action_id": item.action_id}):
        raise HTTPException(status_code=400, detail="ID already exists")
    await db.action_registry.insert_one(item.model_dump())
    RegistryCache.actions.add(item.action_id)
    return item

@router.get("/registries/actions", response_model=List[ActionRegistry])
async def get_actions(db: AsyncIOMotorDatabase = Depends(get_database)):
    return [ActionRegistry(**doc) async for doc in db.action_registry.find()]

# Operator Registry
@router.post("/registries/operators", response_model=OperatorRegistry)
async def create_operator(item: OperatorRegistry, db: AsyncIOMotorDatabase = Depends(get_database)):
    if await db.operator_registry.find_one({"operator_id": item.operator_id}):
        raise HTTPException(status_code=400, detail="ID already exists")
    await db.operator_registry.insert_one(item.model_dump())
    RegistryCache.operators.add(item.operator_id)
    return item

@router.get("/registries/operators", response_model=List[OperatorRegistry])
async def get_operators(db: AsyncIOMotorDatabase = Depends(get_database)):
    return [OperatorRegistry(**doc) async for doc in db.operator_registry.find()]

# Charset Registry
@router.post("/registries/charsets", response_model=CharsetRegistry)
async def create_charset(item: CharsetRegistry, db: AsyncIOMotorDatabase = Depends(get_database)):
    if await db.charset_registry.find_one({"charset_id": item.charset_id}):
        raise HTTPException(status_code=400, detail="ID already exists")
    await db.charset_registry.insert_one(item.model_dump())
    RegistryCache.charsets.add(item.charset_id)
    return item

@router.get("/registries/charsets", response_model=List[CharsetRegistry])
async def get_charsets(db: AsyncIOMotorDatabase = Depends(get_database)):
    return [CharsetRegistry(**doc) async for doc in db.charset_registry.find()]