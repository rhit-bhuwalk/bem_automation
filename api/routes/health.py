from fastapi import APIRouter, HTTPException
from api.database.dtc_descriptions.connection import dtc_db
from api.database.incidents.connection import incident_db

router = APIRouter(
    prefix="/health",
    tags=["Health"]
)

@router.get("/")
async def health_check():
    """
    Check the health of all system components
    """
    try:
        # Check DTC Database
        dtc_status = await dtc_db.is_connected()
        
        # Check Incidents Database
        incident_status = await incident_db.is_connected()
        
        return {
            "status": "healthy" if (dtc_status and incident_status) else "degraded",
            "databases": {
                "dtc_database": {
                    "status": "connected" if dtc_status else "disconnected",
                    "type": "MongoDB",
                    "name": dtc_db.db_name if hasattr(dtc_db, 'db_name') else None,
                    "count": await dtc_db.count_documents(),
                    "latest_doc": await dtc_db.get_latest_document()
                },
                "incidents_database": {
                    "status": "connected" if incident_status else "disconnected",
                    "type": "MongoDB",
                    "name": incident_db.db_name if hasattr(incident_db, 'db_name') else None,
                    "count": await incident_db.count_documents(),
                    "latest_doc": await incident_db.get_latest_document()
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        ) 