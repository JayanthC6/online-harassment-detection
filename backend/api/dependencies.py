from functools import wraps
from flask import request, jsonify
import jwt
from core.config import Config

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
        if not token:
            return jsonify({"error": "Token is missing"}), 401
            
        try:
            secret = Config.JWT_SECRET_KEY
            jwt.decode(token, secret, algorithms=["HS256"])
        except Exception:
            return jsonify({"error": "Token is invalid or expired"}), 401
            
        return f(*args, **kwargs)
    return decorated
