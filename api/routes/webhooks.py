import json
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List
from api.models.IncidentWebhook import IncidentModel, WebhookData, DTCData, AlertData
from api.database.incidents.connection import incident_db
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from api.database.redis.main import redis_db
router = APIRouter()

REQUIRED_FIELDS = ["dtc_data", "alert_data"]

@router.post("/webhooks/dtc")
async def dtc_webhook(payload: WebhookData):
    try:
        payload = DTCData(**payload.data)
        await store_and_maybe_combine(
            event_id=payload.id,
            field_name="dtc_data",
            json_data=payload.model_dump_json(),
            required_fields=REQUIRED_FIELDS
        )
        return {"status": "OK"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/alert")
async def alert_webhook(payload: WebhookData):
    try:
        payload = AlertData(**payload.data)
        await store_and_maybe_combine(
            event_id=payload.id,
            field_name="alert_data",
            json_data=payload.model_dump_json(),
            required_fields=REQUIRED_FIELDS
        )
        return {"status": "OK"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def store_and_maybe_combine(event_id: str, field_name: str, json_data: str, required_fields: List[str]):
    """
    1. Save partial data to Redis under 'incident:{event_id}' with the given field name.
    2. Check if all required fields are present.
    3. If so, combine them into one incident doc, store in Mongo, and remove from Redis.
    """
    key = f"incident:{event_id}"

    try:
        await redis_db.hset(key, field_name, json_data)
        all_data = await redis_db.hgetall(key)
        if all(field in all_data for field in required_fields):
            try:
                dtc_data = json.loads(all_data["dtc_data"])
                alert_data = json.loads(all_data["alert_data"])
                
                dtc_code = dtc_data["type"]
                if dtc_code.startswith("P"):
                    numeric_part = dtc_code[1:4]
                    last_char = dtc_code[4] if len(dtc_code) > 4 else "0"
                    if last_char.isalpha():
                        last_digit = str(ord(last_char.upper()) - ord('A'))
                    else:
                        last_digit = last_char
                    dtc_code = f"{numeric_part}-{last_digit}"
                
                # Convert timestamp from milliseconds to seconds
                timestamp = int(dtc_data["timestamp"] / 1000)
                
                # Parse location string to float values
                lat_str, lon_str = alert_data["location"].split(",")
                lat = float(lat_str)
                lon = float(lon_str)
                
                incident_doc = IncidentModel(
                    id=event_id,  # Set the id field explicitly
                    timestamp=timestamp,
                    account_id=dtc_data["account_id"],
                    vehicle_id=dtc_data["vehicle_id"],
                    vehicle_tag=alert_data["vehicle_tag"],
                    dtc_code=dtc_code,
                    location={"latitude": lat, "longitude": lon}
                )
                
                print(f"Storing incident document: {incident_doc.model_dump_json()}")
                await incident_db.store_incident_data(incident_doc)
                
                await redis_db.delete(key) 
           
            except Exception as e:
                print(f"Error processing incident data: {str(e)}")
                await redis_db.delete(key)
                raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"Error in store_and_maybe_combine: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

