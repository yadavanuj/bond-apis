"""
Hospital Chatbot Onboarding - Seeding Logic

High-Level Proposal:
--------------------
This module seeds the Bond Platform with a realistic configuration for a Hospital AI Chatbot.

1. Workflow:
   - Patient asks a question (INPUT)
   - System retrieves Medical Records (INTERNAL)
   - Data is processed and sent to an LLM for summarization (EXTERNAL)
   - Response is sent back to Patient (EXTERNAL)

2. Governance Strategy:
   - PHI (Protected Health Information) is strictly regulated.
   - PII (Personally Identifiable Information) must be masked before leaving the boundary.
   - Internal steps have full access; External steps (LLM) have restricted access.

3. Taxonomy & Relationships:
   - Patients OWN Appointments and MedicalRecords.
   - Appointments GENERATE MedicalRecords.
   - This graph allows us to trace data lineage and assess blast radius if a record is exposed.
"""

from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from .models import (
    Tenant, Project, Workflow, Step, DirectionEnum, StatusEnum,
    DataModel, FieldModel, FieldCreate, Relationship,
    Policy, Rule, Condition, AppliesTo,
    TypeRegistry, Validation, Structure, Composition, TypeStatusEnum,
)

async def seed_hospital_data(db: AsyncIOMotorDatabase):
    print("🏥 Starting Hospital Domain Seeding...")

    # ---------------------------------------------------------
    # 1. Domain Specific Types
    # ---------------------------------------------------------
    print("   ↳ Seeding Hospital Types...")

    types = [
        TypeRegistry(
            type_id="PATIENT_ID",
            name="Patient Identifier",
            sensitivity="PHI",
            description="Hospital internal patient ID (e.g., PAT-12345678)",
            keywords=["mrn", "patient_id"],
            aliases=["medical_record_number", "patient_no"],
            tags=["healthcare", "identity"],
            validation=Validation(
                regex=["^PAT-\\d{8}$"]
            )
        ),
        TypeRegistry(
            type_id="DIAGNOSIS_CODE",
            name="ICD-10 Code",
            sensitivity="PHI",
            description="International Classification of Diseases code",
            keywords=["icd10", "diagnosis"],
            aliases=["diagnosis_code", "icd_code"],
            tags=["healthcare", "clinical"],
            validation=Validation(
                regex=["^[A-Z]\\d{2}\\.\\d{1,2}$"]
            )
        ),
        TypeRegistry(
            type_id="INSURANCE_ID",
            name="Insurance Policy ID",
            sensitivity="CONFIDENTIAL",
            description="Provider Code (3 chars) + Sequence (6 digits)",
            keywords=["policy_id", "insurance_no"],
            aliases=["insurance_policy_number", "member_id"],
            tags=["healthcare", "financial", "insurance"],
            validation=Validation(
                composition=Composition(
                    structure=[
                        Structure(charset_id="alpha", structural_info={"length": 3, "name": "Provider Code"}),
                        Structure(charset_id="digit", structural_info={"length": 6, "name": "Sequence Number"})
                    ]
                )
            )
        )
    ]

    for t in types:
        t_dict = t.model_dump()
        t_dict["updated_at"] = datetime.utcnow()
        # Upsert based on type_id
        await db.type_registry.update_one({"type_id": t.type_id}, {"$set": t_dict}, upsert=True)

    # ---------------------------------------------------------
    # 2. Tenant & Project
    # ---------------------------------------------------------
    print("   ↳ Seeding Hospital Tenant & Project...")
    
    tenant = Tenant(
        tenant_id="acme-hospital",
        name="Acme General Hospital",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await db.tenants.update_one({"tenant_id": tenant.tenant_id}, {"$set": tenant.model_dump()}, upsert=True)

    project = Project(
        project_id="hospital-support-bot",
        tenant_id="acme-hospital",
        name="Patient Support AI",
        domain="HEALTHCARE",
        description="AI Chatbot for patient queries and lab reports",
        status=StatusEnum.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await db.projects.update_one({"project_id": project.project_id}, {"$set": project.model_dump()}, upsert=True)

    # ---------------------------------------------------------
    # 3. Data Models (The Schema)
    # ---------------------------------------------------------
    print("   ↳ Seeding Hospital Data Models...")

    # Patient Model
    patient_fields = [
        FieldCreate(field_id="p_id", data_type="string", maps_to_type="PATIENT_ID", sensitivity="PHI", notes="Primary Key", scope="PROJECT", scope_id="hospital-support-bot", tags=["identifier", "phi"]),
        FieldCreate(field_id="p_dob", data_type="date", sensitivity="PHI", notes="Date of Birth", scope="PROJECT", scope_id="hospital-support-bot", tags=["phi", "demographic"]),
        FieldCreate(field_id="p_name", data_type="string", sensitivity="PHI", notes="Full Name", scope="PROJECT", scope_id="hospital-support-bot", tags=["phi", "demographic"]),
        FieldCreate(field_id="p_email", data_type="string", maps_to_type="EMAIL", sensitivity="PII", notes="Contact Email", scope="PROJECT", scope_id="hospital-support-bot", tags=["pii", "contact"]),
        FieldCreate(field_id="p_ssn", data_type="string", maps_to_type="SSN", sensitivity="PII", notes="Government ID", scope="PROJECT", scope_id="hospital-support-bot", tags=["pii", "government"]),
        FieldCreate(field_id="p_insurance_id", data_type="string", maps_to_type="INSURANCE_ID", sensitivity="CONFIDENTIAL", notes="Insurance Policy Number", scope="PROJECT", scope_id="hospital-support-bot", tags=["financial", "insurance"]),
    ]

    patient_model = DataModel(
        model_id="patient_record",
        project_id="hospital-support-bot",
        description="Core patient demographic data",
        tags=["core", "phi"],
        fields=[
            # For seeding, we construct the full FieldModel objects
            FieldModel(**f.model_dump(), created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            for f in patient_fields
        ],
        status=StatusEnum.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await db.data_models.update_one({"model_id": patient_model.model_id}, {"$set": patient_model.model_dump()}, upsert=True)

    # Medical Record Model
    med_fields = [
        FieldCreate(field_id="m_id", data_type="string", sensitivity="INTERNAL", notes="Record ID", scope="PROJECT", scope_id="hospital-support-bot", tags=["identifier", "internal"]),
        FieldCreate(field_id="m_pid", data_type="string", maps_to_type="PATIENT_ID", sensitivity="PHI", notes="Foreign Key", scope="PROJECT", scope_id="hospital-support-bot", tags=["phi", "reference"]),
        FieldCreate(field_id="m_diag", data_type="string", maps_to_type="DIAGNOSIS_CODE", sensitivity="PHI", notes="ICD-10", scope="PROJECT", scope_id="hospital-support-bot", tags=["phi", "clinical"]),
        FieldCreate(field_id="m_notes", data_type="string", sensitivity="PHI", notes="Doctor Notes", scope="PROJECT", scope_id="hospital-support-bot", tags=["phi", "unstructured"]),
    ]

    med_model = DataModel(
        model_id="medical_record",
        project_id="hospital-support-bot",
        description="Clinical records and diagnosis",
        tags=["clinical", "phi"],
        fields=[
            FieldModel(**f.model_dump(), created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            for f in med_fields
        ],
        status=StatusEnum.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await db.data_models.update_one({"model_id": med_model.model_id}, {"$set": med_model.model_dump()}, upsert=True)

    # ---------------------------------------------------------
    # 4. Relationships (The Knowledge Graph)
    # ---------------------------------------------------------
    print("   ↳ Seeding Hospital Relationships...")

    rels = [
        Relationship(
            relationship_id="rel_patient_owns_record",
            project_id="hospital-support-bot",
            from_model="patient_record",
            to_model="medical_record",
            relationship_type="OWNS",
            description="Patient owns their medical records",
            tags=["core", "ownership"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]
    for r in rels:
        await db.relationships.update_one({"relationship_id": r.relationship_id}, {"$set": r.model_dump()}, upsert=True)

    # ---------------------------------------------------------
    # 5. Workflow (The Process)
    # ---------------------------------------------------------
    print("   ↳ Seeding Hospital Workflow...")

    workflow = Workflow(
        workflow_id="patient-support-flow",
        project_id="hospital-support-bot",
        name="Patient Inquiry Resolution",
        status=StatusEnum.ACTIVE,
        steps=[
            Step(step_id="STEP_1_INGEST", direction=DirectionEnum.INPUT),
            Step(step_id="STEP_2_FETCH_DATA", direction=DirectionEnum.INTERNAL),
            Step(step_id="STEP_3_LLM_PROCESS", direction=DirectionEnum.EXTERNAL),
            Step(step_id="STEP_4_RESPONSE", direction=DirectionEnum.EXTERNAL),
        ],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    await db.workflows.update_one({"workflow_id": workflow.workflow_id}, {"$set": workflow.model_dump()}, upsert=True)

    # ---------------------------------------------------------
    # 6. Policies (The Guardrails)
    # ---------------------------------------------------------
    print("   ↳ Seeding Hospital Policies...")

    policies = [
        # Policy 1: Block PHI from going to External LLM
        Policy(
            policy_id="pol_block_phi_llm",
            project_id="hospital-support-bot",
            description="Prevent PHI leakage to external LLM providers",
            applies_to=AppliesTo(workflow_id="patient-support-flow", step_id="STEP_3_LLM_PROCESS"),
            rule=Rule(
                conditions=[
                    Condition(operator="sensitivity_in", operand=["PHI"])
                ]
            ),
            action="BLOCK",
            status=StatusEnum.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        # Policy 2: Mask PII for External LLM
        Policy(
            policy_id="pol_mask_pii_llm",
            project_id="hospital-support-bot",
            description="Mask PII before sending to LLM",
            applies_to=AppliesTo(workflow_id="patient-support-flow", step_id="STEP_3_LLM_PROCESS"),
            rule=Rule(
                conditions=[
                    Condition(operator="sensitivity_in", operand=["PII"])
                ]
            ),
            action="MASK",
            status=StatusEnum.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        # Policy 3: Allow PHI for Internal Fetch
        Policy(
            policy_id="pol_allow_phi_internal",
            project_id="hospital-support-bot",
            description="Allow internal systems to process PHI",
            applies_to=AppliesTo(workflow_id="patient-support-flow", step_id="STEP_2_FETCH_DATA"),
            rule=Rule(
                conditions=[
                    Condition(operator="sensitivity_in", operand=["PHI", "PII"])
                ]
            ),
            action="LOG", # Log access but allow it (implicit allow if not blocked)
            status=StatusEnum.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ),
        # Policy 4: Block Insurance IDs specifically (demonstrating type-based rule)
        Policy(
            policy_id="pol_block_insurance_id",
            project_id="hospital-support-bot",
            description="Strictly block Insurance IDs from external LLM",
            applies_to=AppliesTo(workflow_id="patient-support-flow", step_id="STEP_3_LLM_PROCESS"),
            rule=Rule(
                conditions=[
                    Condition(operator="type_is", operand="INSURANCE_ID")
                ]
            ),
            action="BLOCK",
            status=StatusEnum.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]

    for p in policies:
        await db.policies.update_one({"policy_id": p.policy_id}, {"$set": p.model_dump()}, upsert=True)

    print("✅ Hospital Chatbot Onboarding Complete!")
    return {"status": "success", "message": "Hospital data seeded successfully"}