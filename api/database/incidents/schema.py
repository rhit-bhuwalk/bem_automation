from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import time

async def create_indexes(collection):
    await collection.create_index("account_id")
    await collection.create_index("vehicle_id")
    await collection.create_index("timestamp")
    await collection.create_index([("location", "2dsphere")])
    
def create_schema_validation():
    # MongoDB schema validation rules
    incident_schema = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "timestamp", "account_id", "vehicle_id", "vehicle_tag", "dtc_code", "location"],
            "properties": {
                "_id": {
                    "bsonType": "string",
                    "description": "MongoDB document ID"
                },
                "timestamp": {
                    "bsonType": "int",
                    "description": "Unix timestamp when code was raised"
                },
                "account_id": {
                    "bsonType": "string",
                    "description": "Customer identifier"
                },
                "vehicle_id": {
                    "bsonType": "string",
                    "description": "Vehicle identifier"
                },
                "vehicle_tag": {
                    "bsonType": "string",
                    "description": "Vehicle tag number"
                },
                "dtc_code": {
                    "bsonType": "string",
                    "pattern": "^\\d{3}-\\d$",
                    "description": "DTC code in XXX-X format"
                },
                "location": {
                    "bsonType": "object",
                    "required": ["latitude", "longitude"],
                    "properties": {
                        "latitude": {
                            "bsonType": "double",
                            "minimum": -90,
                            "maximum": 90
                        },
                        "longitude": {
                            "bsonType": "double",
                            "minimum": -180,
                            "maximum": 180
                        }
                    }
                }
            },
            "additionalProperties": True
        }
    }
    return incident_schema

async def setup_collection_with_schema():
    # Connect to MongoDB
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client['blue_energy_test']
    
    # Drop collection if exists
    if 'incidents' in await db.list_collection_names():
        await db.incidents.drop()
    
    # Create collection with schema validation
    await db.create_collection("incidents", 
        validator=create_schema_validation()
    )
    
    # Create indexes
    await db.incidents.create_index("account_id")
    await db.incidents.create_index("vehicle_id")
    await db.incidents.create_index("timestamp")
    
    print("Collection created with schema validation")
    return db.incidents

async def test_schema():
    incidents = await setup_collection_with_schema()
    
    # Valid test document
    valid_doc = {
        "timestamp": 1706630400,
        "account_id": "123456789012345", 
        "vehicle_id": "987654321098765",  
        "vehicle_tag": "MH12AB1234",
        "dtc_code": "123-4",
        "location": {
            "latitude": 19.0760,
            "longitude": 72.8777
        },
        "extra_field": "This is allowed now"  
    }
    
    # Invalid test documents
    invalid_docs = [
        # Missing required field
        {
            "account_id": "123456789012345",
            "vehicle_id": "987654321098765",
            "vehicle_tag": "MH12AB1234",
            "dtc_code": "123-4",
            "location": {
                "latitude": 19.0760,
                "longitude": 72.8777
            }
        },
        # Invalid DTC code format
        {
            "timestamp": 1706630400,
            "account_id": "123456789012345",
            "vehicle_id": "987654321098765",
            "vehicle_tag": "MH12AB1234",
            "dtc_code": "1234",  # Wrong format
            "location": {
                "latitude": 19.0760,
                "longitude": 72.8777
            }
        },
        # Invalid location values
        {
            "timestamp": 1706630400,
            "account_id": "123456789012345",
            "vehicle_id": "987654321098765",
            "vehicle_tag": "MH12AB1234",
            "dtc_code": "123-4",
            "location": {
                "latitude": 91.0,  # Invalid latitude (>90)
                "longitude": 72.8777
            }
        }
    ]
    
    print("\nTesting schema validation:")
    
    # Test valid document
    try:
        result = await incidents.insert_one(valid_doc)
        print("✓ Valid document inserted successfully")
        
        # Retrieve and print the inserted document
        inserted_doc = await incidents.find_one({"_id": result.inserted_id})
        print("\nInserted document:")
        print(inserted_doc)
        
    except Exception as e:
        print(f"❌ Error inserting valid document: {str(e)}")
    
    for i, doc in enumerate(invalid_docs):
        try:
            result = await incidents.insert_one(doc)
            print(f"❌ Invalid document {i+1} was inserted (shouldn't happen)")
        except Exception as e:
            print(f"✓ Invalid document {i+1} correctly rejected: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_schema())