from datetime import datetime, timezone, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from core.config import Config
from core.exceptions import AppException
import db


class AuthService:
    @staticmethod
    def authenticate(username: str, password: str) -> str:
        """
        Validate credentials and return a signed JWT.
        Dev passwords (password123) and demo accounts work ONLY when APP_ENV=development.
        In production/any other environment, accept only the hashed admin password from .env.
        """
        role = None

        # ── 1. Demo accounts (only in development) ────────────────────────
        if Config.APP_ENV == "development" and Config.ENABLE_DEMO_ACCOUNTS and Config.DEMO_ACCOUNTS:
            account = Config.DEMO_ACCOUNTS.get(username)
            if account and password == account.get("password"):
                role = account.get("role")

        # ── 2. Admin account ──────────────────────────────────────────────
        if role is None and username == Config.ADMIN_USERNAME:
            if Config.APP_ENV == "development":
                # In development, accept password123 or hashed password
                if password == "password123":
                    role = "Admin"
                elif Config.ADMIN_PASSWORD_HASH and check_password_hash(Config.ADMIN_PASSWORD_HASH, password):
                    role = "Admin"
            else:
                # In non-development, ONLY accept hashed admin password
                if Config.ADMIN_PASSWORD_HASH and check_password_hash(Config.ADMIN_PASSWORD_HASH, password):
                    role = "Admin"

        # ── 3. Database Users ─────────────────────────────────────────────
        if role is None:
            db_user = db.get_user(username)
            if db_user and check_password_hash(db_user.get("password_hash", ""), password):
                role = db_user.get("role", "User")

        if role is None:
            raise AppException("Invalid credentials", status_code=401)

        token = jwt.encode(
            {
                "user": username,
                "role": role,
                "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            },
            Config.JWT_SECRET_KEY,
            algorithm="HS256",  # pinned — alg:none bypass not possible
        )
        return token

    @staticmethod
    def register(username: str, password: str, role: str = "User") -> str:
        """
        Register a new user in the database.
        """
        if not username or not password:
            raise AppException("Username and password are required", status_code=400)

        if db.get_user(username) or (Config.ENABLE_DEMO_ACCOUNTS and username in Config.DEMO_ACCOUNTS) or username == Config.ADMIN_USERNAME:
            raise AppException("Username already taken", status_code=409)

        password_hash = generate_password_hash(password)
        success = db.create_user(username, password_hash, role)
        if not success:
            raise AppException("Could not create user", status_code=500)

        token = jwt.encode(
            {
                "user": username,
                "role": role,
                "exp": datetime.now(timezone.utc) + timedelta(hours=24),
            },
            Config.JWT_SECRET_KEY,
            algorithm="HS256",
        )
        return token
