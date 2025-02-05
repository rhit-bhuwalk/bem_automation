# incidents/connection.py

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from .schema import create_schema_validation, create_indexes
from api.models.IncidentWebhook import IncidentModel
from api.config import DatabaseConfig
import asyncio

# Load environment variables
load_dotenv()

# Get environment variables
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "blue_energy"
if ENVIRONMENT == "test":
    DB_NAME = "blue_energy_test"

class IncidentDatabase:
    client: AsyncIOMotorClient = None
    db = None
    collection = None
    _test_data = {}  # In-memory storage for testing
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB and initialize database"""
        try:
            if os.getenv("ENVIRONMENT") == "test":
                cls._test_data = {}  # Reset test data
                print("Connected to MongoDB - Database: blue_energy_test")
            else:
                # Get the current event loop
                loop = asyncio.get_event_loop()
                
                # Create a new client with the current event loop
                cls.client = AsyncIOMotorClient(
                    DatabaseConfig.uri,
                    io_loop=loop,
                    serverSelectionTimeoutMS=5000
                )
                cls.db = cls.client["blue_energy"]
                collections = await cls.db.list_collection_names()
                
                # Setup collection if it doesn't exist
                if "incidents" not in collections:
                    await cls.db.create_collection(
                        "incidents",
                        validator=create_schema_validation()
                    )
                    await create_indexes(cls.db.incidents)
                
                cls.collection = cls.db.incidents
                print(f"Connected to MongoDB - Database: {cls.db.name}")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise e

    @classmethod
    async def close(cls):
        """Close MongoDB connection"""
        if cls.client and not os.getenv("ENVIRONMENT") == "test":
            cls.client.close()
            print(f"Closed connection to database: {cls.db.name}")

    @classmethod
    async def get_by_vehicle(cls, vehicle_id: str):
        """Get incidents by vehicle ID"""
        if os.getenv("ENVIRONMENT") == "test":
            return [doc for doc in cls._test_data.values() if doc["vehicle_id"] == vehicle_id]
        else:
            cursor = cls.collection.find({"vehicle_id": vehicle_id})
            return await cursor.to_list(length=100)

    @classmethod
    async def get_by_account(cls, account_id: str):
        """Get incidents by account ID"""
        if os.getenv("ENVIRONMENT") == "test":
            return [doc for doc in cls._test_data.values() if doc["account_id"] == account_id]
        else:
            cursor = cls.collection.find({"account_id": account_id})
            return await cursor.to_list(length=100)

    @classmethod
    async def count_documents(cls):
        """Get total number of documents"""
        if os.getenv("ENVIRONMENT") == "test":
            return len(cls._test_data)
        else:
            return await cls.collection.count_documents({})
    
    @classmethod
    async def store_incident_data(cls, payload: IncidentModel):
        """Store incident data"""
        try:
            data = payload.model_dump(by_alias=True)
            if "_id" not in data:
                data["_id"] = str(data.get("incident_id"))
            if os.getenv("ENVIRONMENT") == "test":
                cls._test_data[data["_id"]] = data
            else:
                await cls.collection.insert_one(data)
        except Exception as e:
            print(f"Error storing incident data: {str(e)}")
            raise e

    @classmethod
    async def get_incident_data(cls, incident_id: str):
        """Get incident data by ID"""
        if os.getenv("ENVIRONMENT") == "test":
            return cls._test_data.get(incident_id)
        else:
            return await cls.collection.find_one({"_id": incident_id})
    
    @classmethod
    async def get_latest_document(cls):
        """Get the latest document"""
        if os.getenv("ENVIRONMENT") == "test":
            if not cls._test_data:
                return None
            latest_id = max(cls._test_data.keys())
            return cls._test_data[latest_id]
        else:
            document = await cls.collection.find_one(sort=[("_id", -1)])
            if document and "_id" in document:
                document["_id"] = str(document["_id"])
            return document

    @classmethod
    async def is_connected(cls):
        """Check if the database is connected"""
        if os.getenv("ENVIRONMENT") == "test":
            return True
        else:
            return cls.client is not None

    @classmethod
    async def delete_many(cls, filter_query=None):
        """Delete multiple documents matching the filter query"""
        try:
            if os.getenv("ENVIRONMENT") == "test":
                cls._test_data = {}
                return len(cls._test_data)
            else:
                if filter_query is None:
                    filter_query = {}
                result = await cls.collection.delete_many(filter_query)
                return result.deleted_count
        except Exception as e:
            print(f"Error deleting documents: {e}")
            raise e

incident_db = IncidentDatabase()

# Test connection
async def test_connection():
    try:
        await incident_db.connect()
        count = await incident_db.count_documents()
        print(f"Total incidents: {count}")
        await incident_db.close()
        print("Connection test completed successfully")
    except Exception as e:
        print(f"Connection test failed: {e}")
        raise e

if __name__ == "__main__":
    asyncio.run(test_connection())