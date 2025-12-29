from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from .database import connect_to_mongo, close_mongo_connection, get_database, create_collection_indexes
from .routes import tenant, project, workflow, data_model, relationship, policy, type_registry, registries, seed
from .cache import RegistryCache
from .models import (
    DataModelCreate, PolicyCreate, TypeRegistryCreate, WorkflowCreate,
    PolicyOperatorRegistry, SensitivityRegistry, ActionRegistry, CharsetRegistry,
    TenantCreate, ProjectCreate
)
from .modules.schema_decision_engine import (
    SchemaDecisionEngine, SchemaContext,
    lexical_validation_middleware, symbol_resolution_middleware,
    structural_validation_middleware, semantic_validation_middleware, evolution_validation_middleware
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await create_collection_indexes()
    await RegistryCache.initialize(get_database())
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

# Schema Decision Engine Middleware
@app.middleware("http")
async def schema_enforcement_middleware(request: Request, call_next):
    if request.method in ["POST", "PUT"]:
        path = request.url.path
        model_cls = None
        
        if path.startswith("/data-models"):
            model_cls = DataModelCreate
        elif path.startswith("/policies"):
            model_cls = PolicyCreate
        elif path.startswith("/types"):
            model_cls = TypeRegistryCreate
        elif path.startswith("/workflows"):
            model_cls = WorkflowCreate
        elif path.startswith("/tenants"):
            model_cls = TenantCreate
        elif path.startswith("/projects"):
            model_cls = ProjectCreate
        elif path.startswith("/admin/registries/operators"):
            model_cls = PolicyOperatorRegistry
        elif path.startswith("/admin/registries/sensitivities"):
            model_cls = SensitivityRegistry
        elif path.startswith("/admin/registries/actions"):
            model_cls = ActionRegistry
        elif path.startswith("/admin/registries/charsets"):
            model_cls = CharsetRegistry
            
        if model_cls:
            try:
                # We need to read the body to validate it
                body = await request.body()
                if body:
                    payload = json.loads(body)
                    # Attempt to parse as a full creation model to validate integrity
                    schema_obj = model_cls(**payload)
                    
                    # Compose different middleware pipelines based on schema type or case
                    # Compiler-Grade Pipeline
                    engine = SchemaDecisionEngine()
                    engine.use(lexical_validation_middleware)      # Phase 1: Syntax
                    engine.use(symbol_resolution_middleware)       # Phase 2: Symbols
                    engine.use(structural_validation_middleware)   # Phase 3: Structure
                    engine.use(semantic_validation_middleware)     # Phase 4: Governance
                    engine.use(evolution_validation_middleware)    # Phase 5: Evolution
                    
                    ctx = SchemaContext(schema=schema_obj, proposed_data=payload)
                    ctx = await engine.run(ctx)
                    
                    if ctx.has_errors:
                        return JSONResponse(
                            status_code=400,
                            content={
                                "status": "error",
                                "message": "Schema Validation Failed",
                                "diagnostics": [
                                    {
                                        "severity": d.severity,
                                        "code": d.code,
                                        "entity": d.entity,
                                        "field": d.field,
                                        "value": d.value,
                                        "message": d.message
                                    }
                                    for d in ctx.diagnostics
                                ]
                            }
                        )
            except Exception:
                # If parsing fails or other errors, we let the route handler handle it
                pass
                
    return await call_next(request)

# Include routers
app.include_router(tenant, prefix="/tenants", tags=["tenants"])
app.include_router(project, prefix="/projects", tags=["projects"])
app.include_router(workflow, prefix="/workflows", tags=["workflows"])
app.include_router(data_model, prefix="/data-models", tags=["data-models"])
app.include_router(relationship, prefix="/relationships", tags=["relationships"])
app.include_router(policy, prefix="/policies", tags=["policies"])
app.include_router(type_registry, prefix="/types", tags=["types"])
app.include_router(registries, prefix="/admin", tags=["registries"])
app.include_router(seed, tags=["seed"])

@app.get("/")
async def root():
    return {"message": "Welcome to Bond APIs"}
