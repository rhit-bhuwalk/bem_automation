# config.py
import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev").lower()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")

ENV_TO_DB = {
    "dev": "blue_energy_dev",
    "prod": "blue_energy_prod",
    "production": "blue_energy_prod",  
    "test": "blue_energy_test"
}

DB_NAME = ENV_TO_DB.get(ENVIRONMENT, "blue_energy_dev")

class DatabaseConfig:
    uri = MONGO_URI
    name = DB_NAME
    environment = ENVIRONMENT 
