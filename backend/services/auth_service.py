"""
Authentication service.

JWT tokens carry three claims:
    user  (str)  — username
    role  (str)  — one of "Admin", "Moderator", "Viewer"
    exp   (int)  — expiry (24 h from issue)

Algorithm is pinned to HS256 on both encode and decode sides.
An "alg:none" unsigned-token bypass is therefore not possible.
"""
import datetime
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

        Priority:
          1. Demo accounts (only when ENABLE_DEMO_ACCOUNTS=true).
          2. Real admin account — password compared against the startup hash.

        Raises AppException(401) on any failure.
        """
        role = None

        # ── 1. Demo accounts ──────────────────────────────────────────────
        if Config.ENABLE_DEMO_ACCOUNTS:
            account = Config.DEMO_ACCOUNTS.get(username)
            if account and password == account["password"]:
                role = account["role"]

        # ── 2. Real admin account ─────────────────────────────────────────
        if role is None:
            if (
                username == Config.ADMIN_USERNAME
                and Config.ADMIN_PASSWORD_HASH is not None
                and check_password_hash(Config.ADMIN_PASSWORD_HASH, password)
            ):
                role = "Admin"
                
        # ── 3. Database Users ─────────────────────────────────────────────
        if role is None:
            db_user = db.get_user(username)
            if db_user and check_password_hash(db_user["password_hash"], password):
                role = db_user.get("role", "User")

        if role is None:
            raise AppException("Invalid credentials", status_code=401)

        token = jwt.encode(
            {
                "user": username,
                "role": role,
                # SECURITY: algorithm explicitly pinned to HS256.
                # Never use jwt.decode without specifying algorithms=[].
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
            },
            Config.JWT_SECRET_KEY,
            algorithm="HS256",  # pinned — alg:none bypass not possible
        )
        return token

    @staticmethod
    def register(username: str, password: str, role: str = "User") -> str:
        """
        Register a new user in the database.
        Returns a JWT token on success.
        """
        if db.get_user(username) or (Config.ENABLE_DEMO_ACCOUNTS and username in Config.DEMO_ACCOUNTS) or username == Config.ADMIN_USERNAME:
            raise AppException("Username already exists", status_code=400)
            
        password_hash = generate_password_hash(password)
        success = db.create_user(username, password_hash, role)
        if not success:
            raise AppException("Failed to create user", status_code=500)
            
        return AuthService.authenticate(username, password)
