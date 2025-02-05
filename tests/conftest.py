import pytest
import asyncio
import os
from dotenv import load_dotenv
import nest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient

# Load environment variables for testing
load_dotenv()
os.environ["ENVIRONMENT"] = "test"
os.environ["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017")
os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379")

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

@pytest.fixture(scope="function")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_client() -> AsyncGenerator[TestClient, None]:
    """Create a test client for each test case."""
    from api.main import app
    from api.database.redis.main import redis_db
    from api.database.incidents.connection import incident_db
    
    await redis_db.connect()
    await incident_db.connect()
    
    client = TestClient(app)
    yield client
    
    try:
        await redis_db.flushdb()
        await incident_db.delete_many({})
    finally:
        await redis_db.close()
        await incident_db.close()

@pytest.fixture(autouse=True)
async def setup_and_cleanup() -> AsyncGenerator[None, None]:
    """Setup before and cleanup after each test"""
    from api.database.redis.main import redis_db
    from api.database.incidents.connection import incident_db
    
    await redis_db.connect()
    await incident_db.connect()
    yield
    try:
        await redis_db.flushdb()
        await incident_db.delete_many({})
    finally:
        await redis_db.close()
        await incident_db.close() 