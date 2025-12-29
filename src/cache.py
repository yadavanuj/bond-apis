from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict

class RegistryCache:
    sensitivities = set()
    actions = set()
    policy_operators = set()
    charsets = set()
    types: Dict[str, str] = {}  # type_id -> sensitivity

    @classmethod
    async def initialize(cls, db: AsyncIOMotorDatabase):
        """Load registries into memory"""
        print("Initializing Registry Cache...")
        
        # Clear existing
        cls.sensitivities.clear()
        cls.actions.clear()
        cls.policy_operators.clear()
        cls.charsets.clear()
        cls.types.clear()

        async for doc in db.sensitivity_registry.find({}, {"sensitivity_id": 1}):
            cls.sensitivities.add(doc["sensitivity_id"])
            
        async for doc in db.action_registry.find({}, {"action_id": 1}):
            cls.actions.add(doc["action_id"])
            
        async for doc in db.operator_registry.find({}, {"operator_id": 1}):
            cls.policy_operators.add(doc["operator_id"])
            
        async for doc in db.charset_registry.find({}, {"charset_id": 1}):
            cls.charsets.add(doc["charset_id"])

        async for doc in db.type_registry.find({}, {"type_id": 1, "sensitivity": 1}):
            cls.types[doc["type_id"]] = doc.get("sensitivity", "INTERNAL")
            
        print(f"Cache Loaded: {len(cls.sensitivities)} Sensitivities, {len(cls.actions)} Actions, {len(cls.policy_operators)} Policy Operators, {len(cls.charsets)} Charsets, {len(cls.types)} Types")