import jwt
import datetime
from core.config import Config
from core.exceptions import AppException

class AuthService:
    @staticmethod
    def authenticate(username: str, password: str) -> str:
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            token = jwt.encode(
                {
                    "user": username,
                    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
                },
                Config.JWT_SECRET_KEY,
                algorithm="HS256"
            )
            return token
        raise AppException("Invalid credentials", status_code=401)
