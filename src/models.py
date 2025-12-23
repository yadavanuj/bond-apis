from pydantic import BaseModel, Field as PydanticField
from typing import List, Optional
from datetime import datetime
from enum import Enum

class StatusEnum(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"

class DirectionEnum(str, Enum):
    INPUT = "INPUT"
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"

class SensitivityEnum(str, Enum):
    INTERNAL = "INTERNAL"
    PII = "PII"
    PCI = "PCI"
    CONFIDENTIAL = "CONFIDENTIAL"

class ActionEnum(str, Enum):
    BLOCK = "BLOCK"
    MASK = "MASK"
    REDACT = "REDACT"
    LOG = "LOG"
    ALERT = "ALERT"

# Tenant Model
class Tenant(BaseModel):
    tenant_id: str
    name: str
    created_at: Optional[datetime] = None

class TenantCreate(BaseModel):
    tenant_id: str
    name: str

class TenantUpdate(BaseModel):
    name: Optional[str] = None

# Project Model
class Project(BaseModel):
    project_id: str
    tenant_id: str
    name: str
    domain: str
    description: Optional[str] = None
    version: int = PydanticField(ge=1)
    status: StatusEnum = StatusEnum.DRAFT
    created_at: Optional[datetime] = None

class ProjectCreate(BaseModel):
    project_id: str
    tenant_id: str
    name: str
    domain: str
    description: Optional[str] = None
    version: int = PydanticField(ge=1)
    status: StatusEnum = StatusEnum.DRAFT

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    version: Optional[int] = PydanticField(ge=1)
    status: Optional[StatusEnum] = None

# Workflow Model
class Step(BaseModel):
    step_id: str
    direction: DirectionEnum

class Workflow(BaseModel):
    workflow_id: str
    project_id: str
    name: Optional[str] = None
    version: Optional[int] = None
    status: StatusEnum = StatusEnum.DRAFT
    steps: List[Step]

class WorkflowCreate(BaseModel):
    workflow_id: str
    project_id: str
    name: Optional[str] = None
    version: Optional[int] = None
    status: StatusEnum = StatusEnum.DRAFT
    steps: List[Step]

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[int] = None
    status: Optional[StatusEnum] = None
    steps: Optional[List[Step]] = None

# Field Model
class FieldModel(BaseModel):
    field_id: str
    type: str
    sensitivity: SensitivityEnum
    maps_to_entity: Optional[str] = None
    notes: Optional[str] = None

class FieldCreate(BaseModel):
    field_id: str
    type: str
    sensitivity: SensitivityEnum
    maps_to_entity: Optional[str] = None
    notes: Optional[str] = None

class FieldUpdate(BaseModel):
    type: Optional[str] = None
    sensitivity: Optional[SensitivityEnum] = None
    maps_to_entity: Optional[str] = None
    notes: Optional[str] = None

# DataModel Model
class DataModel(BaseModel):
    model_id: str
    project_id: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    fields: List[FieldModel]
    version: Optional[int] = None
    status: StatusEnum = StatusEnum.DRAFT

class DataModelCreate(BaseModel):
    model_id: str
    project_id: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    fields: List[FieldCreate]
    version: Optional[int] = None
    status: StatusEnum = StatusEnum.DRAFT

class DataModelUpdate(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    fields: Optional[List[FieldUpdate]] = None
    version: Optional[int] = None
    status: Optional[StatusEnum] = None

# Relationship Model
class Relationship(BaseModel):
    relationship_id: str
    project_id: str
    from_model: str
    to_model: str
    type: str
    description: Optional[str] = None

class RelationshipCreate(BaseModel):
    relationship_id: str
    project_id: str
    from_model: str
    to_model: str
    type: str
    description: Optional[str] = None

class RelationshipUpdate(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None

# Policy Model
class AppliesTo(BaseModel):
    workflow_id: Optional[str] = None
    step_id: Optional[str] = None

class Rule(BaseModel):
    deny_if_sensitivity_in: Optional[List[str]] = None

class Policy(BaseModel):
    policy_id: str
    project_id: str
    description: Optional[str] = None
    applies_to: Optional[AppliesTo] = None
    rule: Rule
    action: ActionEnum
    version: Optional[int] = None
    status: StatusEnum = StatusEnum.DRAFT

class PolicyCreate(BaseModel):
    policy_id: str
    project_id: str
    description: Optional[str] = None
    applies_to: Optional[AppliesTo] = None
    rule: Rule
    action: ActionEnum
    version: Optional[int] = None
    status: StatusEnum = StatusEnum.DRAFT

class PolicyUpdate(BaseModel):
    description: Optional[str] = None
    applies_to: Optional[AppliesTo] = None
    rule: Optional[Rule] = None
    action: Optional[ActionEnum] = None
    version: Optional[int] = None
    status: Optional[StatusEnum] = None
