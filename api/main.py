from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from api.routes import webhooks
from api.database.dtc_descriptions.connection import dtc_db
from api.database.incidents.connection import incident_db
from api.routes import health
from api.database.dtc_descriptions.schema import test_schema as test_dtc_schema
from api.database.incidents.schema import test_schema as test_incident_schema
from api.database.redis.main import redis_db
import uvicorn

async def run_startup_tests():
    """Run all database tests before startup"""
    print("\n🔍 Running pre-startup database tests...")
    
    try:
        # Test DTC Database
        print("\nTesting DTC Database Schema:")
        await test_dtc_schema()
        
        # Test Incidents Database
        print("\nTesting Incidents Database:")
        await test_incident_schema()

        print("\n✅ All database schema tests passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Pre-startup tests failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {str(e)}"
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run tests before startup
    try:
        await run_startup_tests()
    except Exception as e:
        print(f"❌ Startup tests failed. Application will not start. Error: {str(e)}")
        raise e
    
    # If tests pass, proceed with normal startup
    print("\nStarting up database connections...")
    await incident_db.connect()
    print("✓ Incidents database connected")
    await dtc_db.connect()
    print("✓ DTC database connected")
    await redis_db.connect()
    print("✓ Redis database connected")
    
    print("\n🚀 Application is ready and running!")
    print("-----------------------------------")
    print("API Documentation: http://localhost:8000/docs")
    print("Alternative Documentation: http://localhost:8000/redoc")
    print("-----------------------------------")
    
    yield
    
    # Shutdown
    print("\nShutting down database connections...")
    await incident_db.close()
    print("✓ Incidents database closed")
    await dtc_db.close()
    print("✓ DTC database closed")

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")

# app.include_router(dtc.router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
