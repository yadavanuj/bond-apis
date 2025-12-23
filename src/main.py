from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import connect_to_mongo, close_mongo_connection
from .routes import tenant, project, workflow, data_model, fields, relationship, policy

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="Bond APIs", description="CRUD APIs for Bond Platform", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tenant, prefix="/tenants", tags=["tenants"])
app.include_router(project, prefix="/projects", tags=["projects"])
app.include_router(workflow, prefix="/workflows", tags=["workflows"])
app.include_router(data_model, prefix="/data-models", tags=["data-models"])
app.include_router(fields, prefix="/fields", tags=["fields"])
app.include_router(relationship, prefix="/relationships", tags=["relationships"])
app.include_router(policy, prefix="/policies", tags=["policies"])

@app.get("/")
async def root():
    return {"message": "Welcome to Bond APIs"}
