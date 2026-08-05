import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.environ.get("MONGODB_URI")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback-secret")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password123")
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:3000").split(",")
    ENABLE_DEMO_ACCOUNTS = os.environ.get("ENABLE_DEMO_ACCOUNTS", "true").lower() == "true"
