from motor.motor_asyncio import AsyncIOMotorDatabase

class RegistryCache:
    sensitivities = set()
    actions = set()
    operators = set()
    charsets = set()

    @classmethod
    async def initialize(cls, db: AsyncIOMotorDatabase):
        """Load registries into memory"""
        print("Initializing Registry Cache...")
        
        # Clear existing
        cls.sensitivities.clear()
        cls.actions.clear()
        cls.operators.clear()
        cls.charsets.clear()

        async for doc in db.sensitivity_registry.find({}, {"sensitivity_id": 1}):
            cls.sensitivities.add(doc["sensitivity_id"])
            
        async for doc in db.action_registry.find({}, {"action_id": 1}):
            cls.actions.add(doc["action_id"])
            
        async for doc in db.operator_registry.find({}, {"operator_id": 1}):
            cls.operators.add(doc["operator_id"])
            
        async for doc in db.charset_registry.find({}, {"charset_id": 1}):
            cls.charsets.add(doc["charset_id"])
            
        print(f"Cache Loaded: {len(cls.sensitivities)} Sensitivities, {len(cls.actions)} Actions, {len(cls.operators)} Operators, {len(cls.charsets)} Charsets")