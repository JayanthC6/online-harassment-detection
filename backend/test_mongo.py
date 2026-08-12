import os
import certifi
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

uri = os.environ.get("MONGODB_URI")
if not uri:
    print("MONGODB_URI not found in environment.")
    exit(1)

print(f"Connecting to MongoDB with tlsCAFile=certifi.where() ({certifi.where()})")

try:
    client = MongoClient(uri, server_api=ServerApi("1"), serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
    client.admin.command("ping")
    print("Connection successful! certifi fixed the issue.")
except Exception as e:
    print(f"Connection failed: {e}")
