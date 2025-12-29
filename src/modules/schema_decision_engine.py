'''
Docstring for src.modules.schema_decision_engine

Schema Decision Engine (Compiler-Grade Validation)

This module acts as the "Compiler Front-End" for the Bond Platform.
It enforces strict governance, structural integrity, and safe evolution rules
across all configuration entities (DataModels, Policies, Workflows).

Architecture:
1. Lexical Phase: Naming conventions and regex patterns.
2. Symbol Resolution: Registry lookups (Sensitivities, Types, Actions).
3. Structural Phase: Cross-entity relationships and integrity.
4. Semantic Phase: Governance rules (e.g., Sensitivity inheritance).
5. Evolution Phase: Diff analysis for versioning and breaking changes.
'''

import re
import logging
from typing import List, Dict, Any, Callable, Optional, Awaitable, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy

from ..models import (
    DataModel, Policy, FieldModel, TypeRegistry,
    DataModelCreate, PolicyCreate, TypeRegistryCreate,
    FieldCreate, StatusEnum, Workflow, WorkflowCreate
)
from ..cache import RegistryCache

logger = logging.getLogger(__name__)

# Sensitivity Hierarchy for Semantic Validation
SENSITIVITY_RANK = {
    "PHI": 4,
    "PII": 3,
    "CONFIDENTIAL": 2,
    "INTERNAL": 1,
    "PUBLIC": 0
}

class DiagnosticSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class Diagnostic:
    """
    Represents a compiler-like message (error/warning) generated during processing.
    Designed to be machine-readable and human-explainable.
    """
    severity: DiagnosticSeverity
    message: str
    code: str
    entity: str
    field: Optional[str] = None
    value: Optional[Any] = None

@dataclass
class SchemaContext:
    """
    The compilation context passed through the middleware chain.
    It holds the inputs (schema, data) and accumulates outputs (diagnostics, metadata).
    """
    schema: Union[DataModel, Policy, TypeRegistry, DataModelCreate, PolicyCreate, TypeRegistryCreate]
    # The baseline data (if updating)
    existing_data: Optional[Dict[str, Any]] = None
    # The proposed changes or new data
    proposed_data: Optional[Dict[str, Any]] = None
    # Active policies to enforce
    policies: List[Policy] = field(default_factory=list)
    
    # Accumulators
    diagnostics: List[Diagnostic] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str, code: str, entity: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.diagnostics.append(Diagnostic(DiagnosticSeverity.ERROR, message, code, entity, field, value))

    def add_warning(self, message: str, code: str, entity: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.diagnostics.append(Diagnostic(DiagnosticSeverity.WARNING, message, code, entity, field, value))

    def add_info(self, message: str, code: str, entity: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.diagnostics.append(Diagnostic(DiagnosticSeverity.INFO, message, code, entity, field, value))

    @property
    def has_errors(self) -> bool:
        return any(d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics)

# Middleware signature: Async function that takes a Context and returns a Context
Middleware = Callable[[SchemaContext], Awaitable[SchemaContext]]

class RegistryResolver:
    """
    Abstraction over the RegistryCache to provide symbol resolution services.
    Ensures the engine does not access the DB directly during validation.
    """
    @staticmethod
    def is_valid_sensitivity(sensitivity_id: str) -> bool:
        return sensitivity_id in RegistryCache.sensitivities

    @staticmethod
    def is_valid_action(action_id: str) -> bool:
        return action_id in RegistryCache.actions

    @staticmethod
    def is_valid_operator(operator_id: str) -> bool:
        return operator_id in RegistryCache.policy_operators

    @staticmethod
    def get_type_sensitivity(type_id: str) -> Optional[str]:
        return RegistryCache.types.get(type_id)


class SchemaDecisionEngine:
    """
    Kernel for schema validation and policy enforcement.
    Executes a chain of functional middlewares to validate, enrich, and check compliance.
    """
    def __init__(self):
        self._middlewares: List[Middleware] = []

    def use(self, middleware: Middleware) -> 'SchemaDecisionEngine':
        """Registers a middleware function to the chain."""
        self._middlewares.append(middleware)
        return self

    async def run(self, context: SchemaContext) -> SchemaContext:
        """
        Executes the middleware chain.
        Catches internal exceptions to ensure the engine always returns a context with diagnostics.
        """
        schema_id = getattr(context.schema, "model_id", None) or \
                    getattr(context.schema, "policy_id", None) or \
                    getattr(context.schema, "type_id", None) or \
                    getattr(context.schema, "workflow_id", None) or "UNKNOWN"
        logger.info(f"Starting Schema Decision Engine for: {schema_id}")
        
        for middleware in self._middlewares:
            try:
                # Pass context through the middleware
                context = await middleware(context)
            except Exception as e:
                logger.exception(f"Middleware failed: {middleware.__name__}")
                context.add_error(f"Internal Engine Error in {middleware.__name__}: {str(e)}", "INTERNAL_ERROR", "Engine")
                # We might choose to break here if the error is catastrophic
                break
        
        return context

# --- Compiler Phases (Middlewares) ---

async def lexical_validation_middleware(ctx: SchemaContext) -> SchemaContext:
    """
    Phase 1: Lexical Validation
    Enforces strict naming conventions and regex patterns on identifiers.
    Rule: ^[a-zA-Z][a-zA-Z0-9_-]{1,63}$
    """
    ID_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{1,63}$")
    
    def check_id(entity_name: str, field_name: str, value: str):
        if not value:
            ctx.add_error(f"{field_name} cannot be empty", "EMPTY_IDENTIFIER", entity_name, field_name, value)
        elif not ID_PATTERN.match(value):
            ctx.add_error(
                f"{field_name} must start with a letter and contain only alphanumeric chars, underscores, or hyphens",
                "INVALID_IDENTIFIER_FORMAT",
                entity_name,
                field_name,
                value
            )

    schema = ctx.schema
    entity_type = type(schema).__name__

    # Check primary IDs
    if hasattr(schema, "model_id"): check_id(entity_type, "model_id", schema.model_id)
    if hasattr(schema, "policy_id"): check_id(entity_type, "policy_id", schema.policy_id)
    if hasattr(schema, "type_id"): check_id(entity_type, "type_id", schema.type_id)
    if hasattr(schema, "workflow_id"): check_id(entity_type, "workflow_id", schema.workflow_id)
    if hasattr(schema, "project_id"): check_id(entity_type, "project_id", schema.project_id)
    if hasattr(schema, "tenant_id"): check_id(entity_type, "tenant_id", schema.tenant_id)
    if hasattr(schema, "operator_id"): check_id(entity_type, "operator_id", schema.operator_id)
    if hasattr(schema, "sensitivity_id"): check_id(entity_type, "sensitivity_id", schema.sensitivity_id)
    if hasattr(schema, "action_id"): check_id(entity_type, "action_id", schema.action_id)
    if hasattr(schema, "charset_id"): check_id(entity_type, "charset_id", schema.charset_id)

    # Check nested IDs (Fields, Steps)
    if isinstance(ctx.schema, (DataModel, DataModelCreate)):
        for f in ctx.schema.fields:
            check_id("Field", "field_id", f.field_id)
    
    elif isinstance(ctx.schema, (Workflow, WorkflowCreate)):
        for s in ctx.schema.steps:
            check_id("Step", "step_id", s.step_id)

    return ctx

async def symbol_resolution_middleware(ctx: SchemaContext) -> SchemaContext:
    """
    Phase 2: Symbol Resolution
    Validates that referenced symbols (Sensitivity, Types, Actions) exist in the Registry.
    """
    schema = ctx.schema
    entity_type = type(schema).__name__

    if isinstance(schema, (DataModel, DataModelCreate)):
        for f in schema.fields:
            # Resolve Sensitivity
            if not RegistryResolver.is_valid_sensitivity(f.sensitivity):
                ctx.add_error(f"Unknown sensitivity: {f.sensitivity}", "UNRESOLVED_SYMBOL", "Field", "sensitivity", f.sensitivity)
            
            # Resolve Type Mapping
            if f.maps_to_type:
                if not RegistryResolver.get_type_sensitivity(f.maps_to_type):
                    ctx.add_error(f"Unknown TypeRegistry ID: {f.maps_to_type}", "UNRESOLVED_SYMBOL", "Field", "maps_to_type", f.maps_to_type)

    elif isinstance(schema, (Policy, PolicyCreate)):
        # Resolve Action
        if not RegistryResolver.is_valid_action(schema.action):
             ctx.add_error(f"Unknown action: {schema.action}", "UNRESOLVED_SYMBOL", "Policy", "action", schema.action)
        
        # Resolve Operators
        if schema.rule and schema.rule.conditions:
            for idx, cond in enumerate(schema.rule.conditions):
                if not RegistryResolver.is_valid_operator(cond.operator):
                    ctx.add_error(f"Unknown operator: {cond.operator}", "UNRESOLVED_SYMBOL", "Condition", "operator", cond.operator)

    elif isinstance(schema, (TypeRegistry, TypeRegistryCreate)):
        # Resolve Sensitivity
        if not RegistryResolver.is_valid_sensitivity(schema.sensitivity):
            ctx.add_error(f"Unknown sensitivity: {schema.sensitivity}", "UNRESOLVED_SYMBOL", "TypeRegistry", "sensitivity", schema.sensitivity)

    return ctx

async def structural_validation_middleware(ctx: SchemaContext) -> SchemaContext:
    """
    Phase 3: Structural Validation
    Validates internal consistency and cross-entity structural rules.
    """
    schema = ctx.schema

    if isinstance(schema, (DataModel, DataModelCreate)):
        # Rule: Field IDs must be unique within a model
        seen_fields = set()
        for f in schema.fields:
            if f.field_id in seen_fields:
                ctx.add_error(f"Duplicate field ID: {f.field_id}", "DUPLICATE_SYMBOL", "DataModel", "fields", f.field_id)
            seen_fields.add(f.field_id)

    elif isinstance(schema, (Policy, PolicyCreate)):
        # Rule: Policy must have at least one condition
        if not schema.rule or not schema.rule.conditions:
             ctx.add_error("Policy must have at least one condition", "EMPTY_RULE", "Policy", "rule")
        
        # Rule: Policy must apply to something (Workflow or Step)
        if not schema.applies_to or (not schema.applies_to.workflow_id and not schema.applies_to.step_id):
             ctx.add_warning("Policy does not apply to any specific target (Global Policy?)", "GLOBAL_POLICY_WARNING", "Policy", "applies_to")

    return ctx

async def semantic_validation_middleware(ctx: SchemaContext) -> SchemaContext:
    """
    Phase 4: Semantic Validation
    Enforces governance rules and logical consistency.
    """
    schema = ctx.schema

    if isinstance(schema, (DataModel, DataModelCreate)):
        for f in schema.fields:
            # Rule: Field cannot downgrade sensitivity below its mapped Type
            if f.maps_to_type:
                type_sensitivity = RegistryResolver.get_type_sensitivity(f.maps_to_type)
                if type_sensitivity:
                    field_rank = SENSITIVITY_RANK.get(f.sensitivity, -1)
                    type_rank = SENSITIVITY_RANK.get(type_sensitivity, -1)
                    
                    # If both are ranked, enforce hierarchy
                    if field_rank != -1 and type_rank != -1:
                        if field_rank < type_rank:
                            ctx.add_error(
                                f"Field sensitivity ({f.sensitivity}) is lower than mapped Type sensitivity ({type_sensitivity})",
                                "SENSITIVITY_DOWNGRADE",
                                "Field",
                                "sensitivity",
                                f.sensitivity
                            )
    
    elif isinstance(ctx.schema, (Policy, PolicyCreate)):
        # Rule: Policies referencing PHI must be careful (Example rule)
        # This would require deeper analysis of the rule conditions
        pass

    return ctx

async def evolution_validation_middleware(ctx: SchemaContext) -> SchemaContext:
    """
    Phase 5: Evolution Validation
    Checks for forbidden schema changes by comparing with existing data.
    """
    # Only applicable if we have existing data (Update scenario)
    if not ctx.existing_data:
        return ctx

    schema = ctx.schema
    existing = ctx.existing_data

    if isinstance(schema, (DataModel, DataModelCreate)):
        # Convert existing fields to a map for easy lookup
        existing_fields = {f["field_id"]: f for f in existing.get("fields", [])}
        new_fields = {f.field_id: f for f in schema.fields}

        # Check for Forbidden Changes
        for f_id, old_field in existing_fields.items():
            if f_id not in new_fields:
                # Field missing in new schema
                # Rule: Silent deletion is forbidden. Must be marked DEPRECATED if removed from active use.
                # However, since the input schema IS the definition, "missing" means deleted.
                # We enforce that you cannot simply remove a field. You must keep it and mark it DEPRECATED.
                # Exception: If the field was already DRAFT? No, let's be strict.
                ctx.add_error(
                    f"Silent deletion of field '{f_id}' is forbidden. Mark as DEPRECATED instead.",
                    "FORBIDDEN_DELETION",
                    "DataModel",
                    "fields",
                    f_id
                )
            else:
                new_field = new_fields[f_id]
                
                # Rule: Cannot change data_type
                if old_field.get("data_type") != new_field.data_type:
                    ctx.add_error(
                        f"Changing data_type for '{f_id}' is forbidden ({old_field.get('data_type')} -> {new_field.data_type})",
                        "FORBIDDEN_EVOLUTION",
                        "Field",
                        "data_type",
                        new_field.data_type
                    )
                
                # Rule: Cannot change maps_to_type
                if old_field.get("maps_to_type") != new_field.maps_to_type:
                    ctx.add_error(
                        f"Changing maps_to_type for '{f_id}' is forbidden",
                        "FORBIDDEN_EVOLUTION",
                        "Field",
                        "maps_to_type",
                        new_field.maps_to_type
                    )

        # Rule: Version Bump Required if fields changed
        # (Simplified check: if existing version >= new version, warn or error)
        existing_version = existing.get("version", 0)
        if schema.version <= existing_version:
             ctx.add_warning(
                 f"Version should be incremented (Current: {existing_version}, New: {schema.version})",
                 "STALE_VERSION",
                 "DataModel",
                 "version",
                 schema.version
             )

    return ctx