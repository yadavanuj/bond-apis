from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime
from ..models import Project, ProjectCreate, ProjectUpdate
from ..database import get_database

router = APIRouter()

@router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    project_dict = project.model_dump()
    project_dict["created_at"] = datetime.utcnow()
    result = await db.projects.insert_one(project_dict)
    project_dict["_id"] = result.inserted_id
    return Project(**project_dict)

@router.get("/projects", response_model=List[Project])
async def get_projects(db: AsyncIOMotorDatabase = Depends(get_database)):
    projects = []
    async for project in db.projects.find():
        projects.append(Project(**project))
    return projects

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    project = await db.projects.find_one({"project_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return Project(**project)

@router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_update: ProjectUpdate, db: AsyncIOMotorDatabase = Depends(get_database)):
    update_data = {k: v for k, v in project_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.projects.update_one({"project_id": project_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    updated_project = await db.projects.find_one({"project_id": project_id})
    return Project(**updated_project)

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.projects.delete_one({"project_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}
