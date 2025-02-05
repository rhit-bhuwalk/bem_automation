from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WebhookData(BaseModel):
    """
    A common Pydantic model for any webhook payload that includes:
      - data: Arbitrary JSON/dict payload
      - action: The action type (e.g. create, update, etc.)
      - entity: The entity type (e.g. trip, vehicle, dtc, alert_log)
    """
    data: Dict[str, Any] = Field(..., description="Arbitrary payload data")
    action: str = Field(..., description="Action type (e.g. create, update)")
    entity: str = Field(..., description="Entity type (e.g. trip, vehicle, dtcs_change_log, alert_log)")

class DTCItem(BaseModel):
    """
    Represents a single item in the 'dtcs' array.
    """
    t: int = Field(..., description="DTC timestamp in epoch ms")
    code: str = Field(..., description="DTC code, e.g., P105C")
    status: int = Field(..., description="Status as an integer (e.g., 1 for active)")

class DTCData(BaseModel):
    """
    Represents the 'data' portion of a DTC webhook payload.
    Mirrors the structure shown in the example:

    {
      "id": "...",
      "timestamp": 1538571507000,
      "account_id": "...",
      "vehicle_id": "...",
      "dtcs": [...],
      "mid": "144",
      "is_sid": true,
      "type": "P105C",
      "status": "active",
      "is_set": true
    }
    """
    id: str = Field(..., description="Unique ID for the DTC record")
    timestamp: int = Field(..., description="Timestamp in epoch ms")
    account_id: str = Field(..., description="Account ID associated with this record")
    vehicle_id: str = Field(..., description="Vehicle ID associated with this record")
    dtcs: List[DTCItem] = Field(..., description="List of DTC items currently set")
    mid: Optional[str] = Field(None, description="Message Identification, if present")
    is_sid: Optional[bool] = Field(None, description="True if SID, false if PID, if present")
    type: str = Field(..., description="The DTC code on which an action happened")
    status: str = Field(..., description="Action that occurred: 'active', 'stored', or 'removed'")
    is_set: bool = Field(..., description="Internal flag to indicate if code is set")

class AlertData(BaseModel):
    """
    Represents the 'data' portion of an Alert webhook payload.
    Mirrors the structure shown in the example:

    {
      "id": "...",
      "account_id": "...",
      "vehicle_id": "...",
      "location": "16.709181666666666,74.28041166666667",
      "timestamp": 1526316669000,
      "vehicle_plate": "AB01CDxxxx",
      "vehicle_tag": "AB 01 CD xxxx",
      "type": "stoppage",
      "alert_values": "{...some JSON string...}",
      "address": "Viman Nagar, Pune"
    }
    """
    id: str = Field(..., description="Unique ID of the corresponding alert")
    account_id: str = Field(..., description="Account ID associated with this alert")
    vehicle_id: str = Field(..., description="Vehicle ID associated with this alert")
    location: str = Field(..., description="String with lat,lng (e.g. '16.70,74.28')")
    timestamp: int = Field(..., description="Epoch timestamp of alert in ms")
    vehicle_plate: str = Field(..., description="Plate of the vehicle")
    vehicle_tag: str = Field(..., description="Tag of the vehicle")
    type: str = Field(..., description="Type of alert (e.g. stoppage, overspeed, etc.)")
    alert_values: str = Field(..., description="Alert-specific values (string containing JSON or text)")
    address: str = Field(..., description="Human-readable address where alert triggered")

class Location(BaseModel):
    latitude: float = Field(
        ...,
        description="Latitude in degrees, must be between -90 and 90.",
        ge=-90,
        le=90
    )
    longitude: float = Field(
        ...,
        description="Longitude in degrees, must be between -180 and 180.",
        ge=-180,
        le=180
    )

class IncidentModel(BaseModel):
    """
    This Pydantic model mirrors your MongoDB schema:
      - id: string (MongoDB document ID)
      - timestamp: Unix timestamp (int)
      - account_id: string
      - vehicle_id: string
      - vehicle_tag: string
      - dtc_code: string in the pattern XXX-X
      - location: nested object with latitude and longitude
    Any additional fields (like 'extra_field') are allowed.
    """
    id: str = Field(
        ...,
        description="MongoDB document ID.",
        alias="_id"
    )
    timestamp: int = Field(
        ...,
        description="Unix timestamp when code was raised."
    )
    account_id: str = Field(
        ...,
        description="Customer identifier."
    )
    vehicle_id: str = Field(
        ...,
        description="Vehicle identifier."
    )
    vehicle_tag: str = Field(
        ...,
        description="Vehicle tag number."
    )
    dtc_code: str = Field(
        ...,
        description="DTC code in XXX-X format.",
    )
    location: Location = Field(
        ...,
        description="Location of the incident with latitude and longitude."
    )

    class Config:
        # Allow extra fields (to match `additionalProperties: true` in MongoDB schema)
        extra = 'allow'
        populate_by_name = True
