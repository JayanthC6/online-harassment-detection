import os
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()


class Config:
    APP_ENV = os.environ.get("APP_ENV", "development").lower()
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "data/shieldai.db")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "shieldai-secret-key-development-placeholder")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")

    # In production, ADMIN_PASSWORD_HASH should be provided directly in .env.
    # Otherwise, derive from ADMIN_PASSWORD at startup if provided.
    _env_hash = os.environ.get("ADMIN_PASSWORD_HASH")
    _raw_admin_password = os.environ.get("ADMIN_PASSWORD", "")

    if _env_hash:
        ADMIN_PASSWORD_HASH = _env_hash
    elif _raw_admin_password:
        ADMIN_PASSWORD_HASH = generate_password_hash(_raw_admin_password)
    elif APP_ENV == "development":
        # Default development password hash for password123
        ADMIN_PASSWORD_HASH = generate_password_hash("password123")
    else:
        ADMIN_PASSWORD_HASH = None

    ALLOWED_ORIGINS = [
        o.strip() for o in os.environ.get(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173"
        ).split(",") if o.strip()
    ]

    # SECURITY: Demo accounts only active in development mode
    ENABLE_DEMO_ACCOUNTS = (
        APP_ENV == "development"
        and os.environ.get("ENABLE_DEMO_ACCOUNTS", "false").lower() == "true"
    )

    DEMO_ACCOUNTS = {
        "admin":     {"password": "password123", "role": "Admin"},
        "moderator": {"password": "password123", "role": "Moderator"},
        "viewer":    {"password": "password123", "role": "Viewer"},
    } if ENABLE_DEMO_ACCOUNTS else {}
