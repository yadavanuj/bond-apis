from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from ..models import Workflow, WorkflowCreate, WorkflowUpdate
from ..database import get_database

router = APIRouter()

@router.post("/workflows", response_model=Workflow)
async def create_workflow(workflow: WorkflowCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    workflow_dict = workflow.model_dump()
    result = await db.workflows.insert_one(workflow_dict)
    workflow_dict["_id"] = result.inserted_id
    return Workflow(**workflow_dict)

@router.get("/workflows", response_model=List[Workflow])
async def get_workflows(db: AsyncIOMotorDatabase = Depends(get_database)):
    workflows = []
    async for workflow in db.workflows.find():
        workflows.append(Workflow(**workflow))
    return workflows

@router.get("/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    workflow = await db.workflows.find_one({"workflow_id": workflow_id})
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return Workflow(**workflow)

@router.put("/workflows/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: str, workflow_update: WorkflowUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = {k: v for k, v in workflow_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.workflows.update_one({"workflow_id": workflow_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Workflow not found")
    updated_workflow = await db.workflows.find_one({"workflow_id": workflow_id})
    return Workflow(**updated_workflow)

@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.workflows.delete_one({"workflow_id": workflow_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"message": "Workflow deleted successfully"}
