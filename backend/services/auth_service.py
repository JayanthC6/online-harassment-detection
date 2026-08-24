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
from werkzeug.security import check_password_hash

from core.config import Config
from core.exceptions import AppException


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
