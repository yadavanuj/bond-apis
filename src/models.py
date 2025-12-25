"""
Domain Models for the Bond Platform.

This module defines the core entities and value objects used throughout the system.
It includes configuration models (Tenant, Project), structural models (DataModel, Field),
logic models (Policy, Workflow), and the Type Registry system for deep data validation.

All persisted models include audit timestamps (created_at, updated_at) and versioning
where applicable to support optimistic concurrency control.
"""
from pydantic import BaseModel, Field as PydanticField
from typing import List, Optional, Any, Union, Dict, Literal
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

class TypeStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"

# Tenant Model
# The root entity representing a customer or organization.
# All Projects and resources belong to a Tenant.
class Tenant(BaseModel):
    tenant_id: str
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TenantCreate(BaseModel):
    tenant_id: str
    name: str

class TenantUpdate(BaseModel):
    name: Optional[str] = None

# Project Model
# A logical workspace within a Tenant.
# Acts as a container for Workflows, DataModels, and Policies.
class Project(BaseModel):
    project_id: str
    tenant_id: str
    name: str
    domain: str
    description: Optional[str] = None
    version: int = PydanticField(default=1, ge=1)
    status: StatusEnum = StatusEnum.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProjectCreate(BaseModel):
    project_id: str
    tenant_id: str
    name: str
    domain: str
    description: Optional[str] = None
    version: int = PydanticField(default=1, ge=1)
    status: StatusEnum = StatusEnum.DRAFT

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    version: Optional[int] = PydanticField(ge=1)
    status: Optional[StatusEnum] = None

# Workflow Model
# Represents a data processing pipeline.
# Composed of a sequence of Steps that data flows through.
class Step(BaseModel):
    step_id: str
    direction: DirectionEnum

# The definition of a data flow.
# Policies can be attached to the Workflow as a whole or individual Steps.
class Workflow(BaseModel):
    workflow_id: str
    project_id: str
    name: Optional[str] = None
    version: int = PydanticField(default=1, ge=1)
    status: StatusEnum = StatusEnum.DRAFT
    steps: List[Step]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class WorkflowCreate(BaseModel):
    workflow_id: str
    project_id: str
    name: Optional[str] = None
    version: int = PydanticField(default=1, ge=1)
    status: StatusEnum = StatusEnum.DRAFT
    steps: List[Step]

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[int] = None
    status: Optional[StatusEnum] = None
    steps: Optional[List[Step]] = None

# Field Model
# Represents a single data attribute (column/property).
# - data_type: The structural type (e.g., "string", "integer") or a reference to a TypeRegistry ID.
# - sensitivity: The classification level (e.g., "PII", "CONFIDENTIAL") backed by SensitivityRegistry.
# - maps_to_type: Optional mapping to a standardized enterprise type.
class FieldModel(BaseModel):
    field_id: str
    data_type: str
    sensitivity: str
    maps_to_type: Optional[str] = None
    notes: Optional[str] = None
    scope: Literal["SYSTEM", "GLOBAL", "TENANT", "PROJECT"]
    scope_id: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FieldCreate(BaseModel):
    field_id: str
    data_type: str
    sensitivity: str
    maps_to_type: Optional[str] = None
    notes: Optional[str] = None
    scope: Literal["SYSTEM", "GLOBAL", "TENANT", "PROJECT"]
    scope_id: Optional[str] = None
    tags: Optional[List[str]] = None

class FieldUpdate(BaseModel):
    data_type: Optional[str] = None
    sensitivity: Optional[str] = None
    maps_to_type: Optional[str] = None
    notes: Optional[str] = None
    scope: Optional[Literal["SYSTEM", "GLOBAL", "TENANT", "PROJECT"]] = None
    scope_id: Optional[str] = None
    tags: Optional[List[str]] = None

# DataModel Model
# Represents a schema, table, or object definition.
# Acts as an Aggregate Root for a collection of Fields.
class DataModel(BaseModel):
    model_id: str
    project_id: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    fields: List[FieldModel]
    version: int = PydanticField(default=1, ge=1)
    status: StatusEnum = StatusEnum.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DataModelCreate(BaseModel):
    model_id: str
    project_id: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    fields: List[FieldCreate]
    version: int = PydanticField(default=1, ge=1)
    status: StatusEnum = StatusEnum.DRAFT

class DataModelUpdate(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    fields: Optional[List[FieldCreate]] = None
    version: Optional[int] = None
    status: Optional[StatusEnum] = None

# Relationship Model
# Defines a directed semantic link between two DataModels.
# e.g., "Customer (from) OWNS (type) Order (to)".
class Relationship(BaseModel):
    relationship_id: str
    project_id: str
    from_model: str
    to_model: str
    relationship_type: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class RelationshipCreate(BaseModel):
    relationship_id: str
    project_id: str
    from_model: str
    to_model: str
    relationship_type: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class RelationshipUpdate(BaseModel):
    relationship_type: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

# Policy Model
# Defines governance rules (Authorization, Privacy, Quality).
# Can apply to specific Workflows or Steps.
class AppliesTo(BaseModel):
    workflow_id: Optional[str] = None
    step_id: Optional[str] = None

# A single logical check within a Rule.
# operator: The logic function (e.g., "equals", "contains_pii") backed by PolicyOperatorRegistry.
# operand: The value(s) to check against.
class Condition(BaseModel):
    operator: str
    operand: Any

# A collection of Conditions that must all evaluate to true (AND logic).
class Rule(BaseModel):
    conditions: List[Condition]

class Policy(BaseModel):
    policy_id: str
    project_id: str
    description: Optional[str] = None
    applies_to: Optional[AppliesTo] = None
    rule: Rule
    action: str
    version: int = PydanticField(default=1, ge=1)
    status: StatusEnum = StatusEnum.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PolicyCreate(BaseModel):
    policy_id: str
    project_id: str
    description: Optional[str] = None
    applies_to: Optional[AppliesTo] = None
    rule: Rule
    action: str
    version: int = PydanticField(default=1, ge=1)
    status: StatusEnum = StatusEnum.DRAFT

class PolicyUpdate(BaseModel):
    description: Optional[str] = None
    applies_to: Optional[AppliesTo] = None
    rule: Optional[Rule] = None
    action: Optional[str] = None
    version: Optional[int] = None
    status: Optional[StatusEnum] = None

# Type Registry Model
# The Type Registry is the central catalog for data definitions.
# It allows defining complex validation rules that can be reused across Fields.

class LengthConstraint(BaseModel):
    exact: Optional[int] = None
    min: Optional[int] = None
    max: Optional[int] = None

# Defines a specific segment of a structured data type.
# Used for composite types like Credit Cards or License Plates.
# - charset_id: The allowed vocabulary for this segment (e.g., "DIGIT", "HEX").
# - structural_info: Metadata enforcing structure (e.g., length, padding).
class Structure(BaseModel):
    charset_id: str
    structural_info: Optional[Union[Dict[str, Any], List[Any]]] = None

# Container for structural rules.
class Composition(BaseModel):
    structure: Optional[List[Structure]] = None

# Comprehensive validation logic for a Type.
# - length: Basic size constraints.
# - charset: The global set of allowed characters (Vocabulary).
# - regex: Pattern matching for format validation (Syntax).
# - checksum: Algorithmic integrity checks (e.g., Luhn, Mod10).
# - composition: Detailed breakdown of internal structure.
class Validation(BaseModel):
    length: Optional[LengthConstraint] = None
    charset: Optional[str] = None
    regex: Optional[List[str]] = None
    checksum: Optional[str] = None
    composition: Optional[Composition] = None

# The definition of a reusable Data Type.
# - category_id: Semantic grouping (e.g., "PII", "FINANCIAL") backed by TypeCategoryRegistry.
# - validation: The rules engine configuration for this type.
class TypeRegistry(BaseModel):
    type_id: str
    name: str
    sensitivity: str
    description: Optional[str] = None
    validation: Validation
    keywords: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    version: int = PydanticField(default=1, ge=1)
    status: Optional[TypeStatusEnum] = TypeStatusEnum.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TypeRegistryCreate(BaseModel):
    type_id: str
    name: str
    sensitivity: str
    description: Optional[str] = None
    validation: Validation
    keywords: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    version: int = PydanticField(default=1, ge=1)
    status: Optional[TypeStatusEnum] = TypeStatusEnum.ACTIVE

class TypeRegistryUpdate(BaseModel):
    name: Optional[str] = None
    sensitivity: Optional[str] = None
    description: Optional[str] = None
    validation: Optional[Validation] = None
    keywords: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    version: Optional[int] = PydanticField(ge=1, default=None)
    status: Optional[TypeStatusEnum] = None

# Dynamic Registries
# These models support the extensibility of the platform, allowing
# new sensitivities, actions, operators, and charsets to be defined at runtime.
class SensitivityRegistry(BaseModel):
    sensitivity_id: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ActionRegistry(BaseModel):
    action_id: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PolicyOperatorRegistry(BaseModel):
    operator_id: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CharsetRegistry(BaseModel):
    charset_id: str
    description: Optional[str] = None
    characters: Optional[str] = None
    patterns: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
