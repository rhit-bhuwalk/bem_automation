# app/database/dtc_schema.py

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import time

def create_schema_validation():
    """Create MongoDB schema validation rules for DTC Descriptions"""
    dtc_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "Name", 
                "Title", 
                "DTC", 
                "Component", 
                "SEVERITY",
                "Driver_reaction",
                "Test_Condition",
                "Fault_Detection",
                "Performance_Limiter",
                "Residual_torque",
                "RED_LAMP",
                "Amber_Lamp",
                "MIL",
                "Validation",
                "Healing"
            ],
            "properties": {
                "Name": {
                    "bsonType": "string",
                    "description": "Name of the system (e.g., ACOOL)"
                },
                "Title": {
                    "bsonType": "string",
                    "description": "Description of the issue"
                },
                "DTC": {
                    "bsonType": "string",
                    "description": "DTC code"
                },
                "Component": {
                    "bsonType": "string",
                    "description": "Affected component"
                },
                "SEVERITY": {
                    "bsonType": "string",
                    "enum": ["low", "medium", "high", "major", "critical"],
                    "description": "Criticality of the issue (low, medium, high, major, or critical)"
                },
                "Driver_reaction": {
                    "bsonType": "string",
                    "description": "Required driver response"
                },
                "Test_Condition": {
                    "bsonType": "string",
                    "description": "Conditions for test"
                },
                "Fault_Detection": {
                    "bsonType": "string",
                    "description": "Fault detection conditions"
                },
                "Performance_Limiter": {
                    "bsonType": "string",
                    "description": "Performance limitation details"
                },
                "Residual_torque": {
                    "bsonType": ["int", "string"],
                    "description": "Residual torque percentage"
                },
                "RED_LAMP": {
                    "bsonType": "string",
                    "enum": ["ON", "OFF"],
                    "description": "Red lamp status"
                },
                "Amber_Lamp": {
                    "bsonType": "string",
                    "enum": ["ON", "OFF"],
                    "description": "Amber lamp status"
                },
                "MIL": {
                    "bsonType": "string",
                    "enum": ["ON", "OFF"],
                    "description": "MIL status"
                },
                "Validation": {
                    "bsonType": "string",
                    "description": "Validation conditions (MIL ON)"
                },
                "Healing": {
                    "bsonType": "string",
                    "description": "Healing conditions (MIL OFF)"
                }
            },
            "additionalProperties": True
        }
    }
    return dtc_schema

async def create_indexes(collection):
    """Create necessary indexes for DTC collection"""
    await collection.create_index("DTC", unique=True)
    await collection.create_index("Name")
    await collection.create_index("SEVERITY")
    await collection.create_index("Component")

async def setup_test_collection():
    """Setup test collection with schema and run tests"""
    # Connect to MongoDB
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client['DTC_Descriptions_Test']
    
    # Create collection with schema validation
    if 'dtc_codes' in await db.list_collection_names():
        await db.dtc_codes.drop()
    
    await db.create_collection('dtc_codes', validator=create_schema_validation())
    collection = db.dtc_codes
    
    # Create indexes
    await create_indexes(collection)
    
    return collection

async def test_schema():
    collection = await setup_test_collection()
    
    # Valid test document
    valid_doc = {
        "Name": "ACOOL",
        "Title": "Air Cooling System Efficiency: Low efficiency",
        "DTC": "2630-0",
        "Component": "Intercooler",
        "SEVERITY": "major",
        "Driver_reaction": "Continue to service station",
        "Test_Condition": "Monitoring is active",
        "Fault_Detection": "ECU initialized",
        "Performance_Limiter": "Temperature threshold",
        "Residual_torque": "80",
        "RED_LAMP": "OFF",
        "Amber_Lamp": "ON",
        "MIL": "ON",
        "Validation": "2 Driving cycle",
        "Healing": "3 Driving cycle"
    }
    
    # Invalid test documents
    invalid_docs = [
        # Missing required field
        {
            "Name": "ACOOL",
            "Title": "Air Cooling System Efficiency",
            "Component": "Intercooler"
        },
        # Invalid DTC format
        {
            **valid_doc,
            "DTC": "123"  # Wrong format
        },
        # Invalid severity value
        {
            **valid_doc,
            "SEVERITY": "mediumly"  # Not in enum
        },
        # Invalid lamp value
        {
            **valid_doc,
            "RED_LAMP": "BLINKING"  # Not in enum
        },
        # Additional property
        {
            **valid_doc,
            "extra_field": "not allowed"
        }
    ]
    
    print("\nRunning schema validation tests:")
    
    # Test valid document
    try:
        result = await collection.insert_one(valid_doc)
        print("✓ Valid document inserted successfully")
        
        # Verify retrieval
        retrieved = await collection.find_one({"DTC": "2630-0"})
        print(f"✓ Document retrieved successfully with DTC: {retrieved['DTC']}")
        
    except Exception as e:
        print(f"❌ Error with valid document: {str(e)}")
    
    # Test invalid documents
    for i, doc in enumerate(invalid_docs, 1):
        try:
            result = await collection.insert_one(doc)
            print(f"❌ Invalid document {i} was inserted (shouldn't happen)")
        except Exception as e:
            print(f"✓ Invalid document {i} correctly rejected: {type(e).__name__}")
    
    # Test index uniqueness
    try:
        await collection.insert_one(valid_doc)  # Try to insert same DTC code
        print("❌ Duplicate DTC code was inserted (shouldn't happen)")
    except Exception as e:
        print("✓ Duplicate DTC code correctly rejected")

if __name__ == "__main__":
    asyncio.run(test_schema())