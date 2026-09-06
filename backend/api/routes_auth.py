from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from core.exceptions import AppException
from extensions import limiter

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/register", methods=["POST"])
@limiter.limit("5 per minute")
def auth_register():
    """Public - register a new standard User."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
        
    try:
        # Enforce role="User" strictly
        token = AuthService.register(username, password, role="User")
        return jsonify({"token": token, "message": "Registration successful"})
    except AppException as e:
        return jsonify({"error": str(e)}), e.status_code
