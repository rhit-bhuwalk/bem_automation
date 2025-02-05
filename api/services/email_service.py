# import os
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail, Email, To, Content
# from typing import List
# import dotenv

# dotenv.load_dotenv()

# SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
# FROM_EMAIL = os.getenv("FROM_EMAIL")

# if not SENDGRID_API_KEY or not FROM_EMAIL:
#     raise ValueError("Missing SendGrid configuration. Please set SENDGRID_API_KEY and FROM_EMAIL environment variables.")

# sg = SendGridAPIClient(SENDGRID_API_KEY)

# async def send_dtc_alert(
#     to_emails: List[str],
#     vehicle_id: str,
#     dtc_codes: List[str],
#     timestamp: str,
#     status: str
# ) -> bool:
#     """
#     Sends a DTC alert email using SendGrid.
    
#     Args:
#         to_emails: List of recipient email addresses
#         vehicle_id: ID of the vehicle that triggered the DTC
#         dtc_codes: List of DTC codes that were triggered
#         timestamp: Timestamp of the DTC event
#         status: Status of the DTC (active/stored)
    
#     Returns:
#         bool: True if email was sent successfully
#     """
#     try:
#         # Create email content
#         subject = f"DTC Alert: New DTCs detected for Vehicle {vehicle_id}"
#         html_content = f"""
#         <h2>DTC Alert Notification</h2>
#         <p>New DTCs have been detected for vehicle {vehicle_id}</p>
#         <p><strong>Time:</strong> {timestamp}</p>
#         <p><strong>Status:</strong> {status}</p>
#         <p><strong>DTC Codes:</strong></p>
#         <ul>
#             {"".join(f"<li>{code}</li>" for code in dtc_codes)}
#         </ul>
#         """
        
#         # Create message
#         message = Mail(
#             from_email=FROM_EMAIL,
#             subject=subject,
#             html_content=html_content
#         )
        
#         # Add all recipients
#         for email in to_emails:
#             message.add_to(To(email))
            
#         # Send email
#         response = sg.send(message)
#         return response.status_code == 202
        
#     except Exception as e:
#         print(f"Failed to send email: {str(e)}")
#         return False 