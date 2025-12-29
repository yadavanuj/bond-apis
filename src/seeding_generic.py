"""
Generic Data Seeding Logic

This module seeds the Bond Platform with domain-agnostic configuration.
It includes:
- Dynamic Registries (Charsets, Sensitivities, Actions, Operators)
- Common Types (SSN, EMAIL, CREDIT_CARD)
"""

from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from .models import (
    TypeRegistry, Validation,
    SensitivityRegistry, ActionRegistry, PolicyOperatorRegistry,
    CharsetRegistry
)

async def seed_generic_data(db: AsyncIOMotorDatabase):
    print("🌍 Starting Generic Data Seeding...")

    # ---------------------------------------------------------
    # 1. Dynamic Registries (The Vocabulary)
    # ---------------------------------------------------------
    print("   ↳ Seeding Core Registries...")
    
    # Charsets
    charsets = [
        {"charset_id": "digit", "description": "Numeric digits 0-9", "characters": "0123456789"},
        {"charset_id": "alpha", "description": "Alphabetic characters", "characters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"},
        {"charset_id": "alphanumeric", "description": "Alphanumeric", "characters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"},
        {"charset_id": "hex", "description": "Hexadecimal", "characters": "0123456789ABCDEFabcdef"},
        {"charset_id": "any", "description": "Any character", "characters": None},
    ]
    for c in charsets:
        c["created_at"] = datetime.now(timezone.utc)
        c["updated_at"] = datetime.now(timezone.utc)
        await db.charset_registry.update_one({"charset_id": c["charset_id"]}, {"$set": c}, upsert=True)

    # Sensitivities
    sensitivities = [
        {"sensitivity_id": "PHI", "description": "Protected Health Information (HIPAA)"},
        {"sensitivity_id": "PII", "description": "Personally Identifiable Information"},
        {"sensitivity_id": "CONFIDENTIAL", "description": "Business Confidential"},
        {"sensitivity_id": "INTERNAL", "description": "Internal Use Only"},
        {"sensitivity_id": "PUBLIC", "description": "Publicly Available"},
    ]
    for s in sensitivities:
        s["created_at"] = datetime.now(timezone.utc)
        s["updated_at"] = datetime.now(timezone.utc)
        await db.sensitivity_registry.update_one({"sensitivity_id": s["sensitivity_id"]}, {"$set": s}, upsert=True)

    # Actions
    actions = [
        {"action_id": "BLOCK", "description": "Stop the workflow execution"},
        {"action_id": "MASK", "description": "Replace characters with *"},
        {"action_id": "REDACT", "description": "Remove the field entirely"},
        {"action_id": "LOG", "description": "Log the access for audit"},
    ]
    for a in actions:
        a["created_at"] = datetime.now(timezone.utc)
        a["updated_at"] = datetime.now(timezone.utc)
        await db.action_registry.update_one({"action_id": a["action_id"]}, {"$set": a}, upsert=True)

    # Operators
    operators = [
        {"operator_id": "equals", "description": "Exact match"},
        {"operator_id": "contains", "description": "Substring match"},
        {"operator_id": "sensitivity_in", "description": "Check if field sensitivity is in list"},
        {"operator_id": "type_is", "description": "Check if field type matches"},
    ]
    for o in operators:
        o["created_at"] = datetime.now(timezone.utc)
        o["updated_at"] = datetime.now(timezone.utc)
        await db.operator_registry.update_one({"operator_id": o["operator_id"]}, {"$set": o}, upsert=True)

    # ---------------------------------------------------------
    # 2. Common Types (The Dictionary)
    # ---------------------------------------------------------
    print("   ↳ Seeding Common Types...")
    
    types = [
        TypeRegistry(
            type_id="SSN",
            name="Social Security Number",
            sensitivity="PII",
            description="US Social Security Number",
            keywords=["ssn", "social_security"],
            aliases=["social_security_number", "tax_id"],
            tags=["pii", "government", "identity"],
            validation=Validation(
                regex=["^\\d{3}-\\d{2}-\\d{4}$"]
            )
        ),
        TypeRegistry(
            type_id="EMAIL",
            name="Email Address",
            sensitivity="PII",
            description="Standard email format",
            keywords=["email", "e-mail", "mail"],
            aliases=["email_address", "contact_email"],
            tags=["pii", "communication"],
            validation=Validation(
                regex=["^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"]
            )
        ),
        TypeRegistry(
            type_id="CREDIT_CARD",
            name="Credit Card Number",
            sensitivity="CONFIDENTIAL",
            description="Payment card number with Luhn check",
            keywords=["card_number", "cc_num"],
            aliases=["credit_card", "debit_card", "pan"],
            tags=["financial", "pci"],
            validation=Validation(
                checksum="LUHN",
                regex=["^\\d{16}$"]
            )
        )
    ]

    for t in types:
        t_dict = t.model_dump()
        t_dict["created_at"] = datetime.now(timezone.utc)
        t_dict["updated_at"] = datetime.now(timezone.utc)
        # Upsert based on type_id
        await db.type_registry.update_one({"type_id": t.type_id}, {"$set": t_dict}, upsert=True)

    print("✅ Generic Data Seeding Complete!")
    return {"status": "success", "message": "Generic data seeded successfully"}