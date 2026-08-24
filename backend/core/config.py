import os
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()


class Config:
    MONGODB_URI = os.environ.get("MONGODB_URI")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "fallback-secret")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")

    # ADMIN_PASSWORD is used ONLY at startup to derive a hash.
    # It is never compared as plaintext anywhere in the application.
    _raw_admin_password = os.environ.get("ADMIN_PASSWORD", "")
    ADMIN_PASSWORD_HASH = generate_password_hash(_raw_admin_password) if _raw_admin_password else None

    ALLOWED_ORIGINS = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://localhost:3000"
    ).split(",")

    # SECURITY: defaults to False. Must be explicitly set to "true" in .env
    # for local development. NEVER enable on a deployed or client-facing instance.
    ENABLE_DEMO_ACCOUNTS = os.environ.get("ENABLE_DEMO_ACCOUNTS", "false").lower() == "true"

    # Demo account credentials — non-dictionary passwords for local dev only.
    # These are only active when ENABLE_DEMO_ACCOUNTS=true.
    DEMO_ACCOUNTS = {
        "admin":     {"password": "Sh13ldAI!Dev#2026", "role": "Admin"},
        "moderator": {"password": "Mod3r@t0r!Shld",   "role": "Moderator"},
        "viewer":    {"password": "V13w0nly!Shld",     "role": "Viewer"},
    }
