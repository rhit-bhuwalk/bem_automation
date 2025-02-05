# from api.dependencies.supabase import supabase
# from api.models.DTCWebhook import DTCWebhook
# from datetime import datetime
# from api.services.email_service import send_dtc_alert
# import os

# # Get alert recipients from environment variable
# ALERT_RECIPIENTS = os.getenv("DTC_ALERT_RECIPIENTS", "").split(",")

# async def store_dtc_data(payload: DTCWebhook):
#     """
#     Stores relevant DTC data in Supabase and sends email alerts.
#     """
#     dtc_data = payload.data
    
#     # Collect DTC codes for email
#     dtc_codes = [dtc.code for dtc in dtc_data.dtcs]
#     timestamp = datetime.fromtimestamp(dtc_data.timestamp / 1000).isoformat()
    
#     # Store data in Supabase
#     for dtc in dtc_data.dtcs:
#         record = {
#             "vehicle_id": dtc_data.vehicle_id,
#             "account_id": dtc_data.account_id,
#             "dtc_code": dtc.code,
#             "dtc_status": dtc.status,
#             "timestamp": datetime.fromtimestamp(dtc.t / 1000).isoformat(),
#             "event_id": dtc_data.id,
#             "dtc_type": dtc_data.type,
#             "is_active": dtc_data.status == "active",
#             "created_at": datetime.utcnow().isoformat()
#         }
        
#         data = supabase.table("dtc_events").insert(record).execute()
    
#     # Send email alert if recipients are configured
#     if ALERT_RECIPIENTS and payload.action == "create":
#         await send_dtc_alert(
#             to_emails=ALERT_RECIPIENTS,
#             vehicle_id=dtc_data.vehicle_id,
#             dtc_codes=dtc_codes,
#             timestamp=timestamp,
#             status=dtc_data.status
#         )
    
#     return True 