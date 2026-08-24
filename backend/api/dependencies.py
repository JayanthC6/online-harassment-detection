"""
Request-level auth decorators for admin routes.

token_required:
    Validates the Bearer JWT in Authorization header.
    Returns 401 on missing or invalid token.
    Injects the decoded payload as `token_data` kwarg into the wrapped function.

require_role(*roles):
    Must be stacked INSIDE token_required (i.e. listed after it).
    Returns 403 (not 401) when the token is valid but the role is insufficient.
    403 vs 401 distinction is intentional:
        401 = unauthenticated (no token or bad token)
        403 = authenticated but unauthorised (valid token, wrong role)

Algorithm is pinned to HS256. An "alg:none" bypass is not possible.
"""
from functools import wraps
import jwt
from flask import request, jsonify
from core.config import Config


def token_required(f):
    """Enforce JWT authentication. Injects token_data into the wrapped view."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            # SECURITY: algorithms list is explicit — alg:none bypass is blocked.
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid"}), 401

        kwargs["token_data"] = payload
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    """
    Decorator factory. Restrict an endpoint to the given role(s).
    Must be applied AFTER @token_required (i.e. closer to the function).

    Returns 403 when the authenticated user lacks the required role.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token_data = kwargs.get("token_data", {})
            user_role = token_data.get("role", "")
            if user_role not in roles:
                return jsonify({
                    "error": f"Forbidden: requires one of {list(roles)}, got '{user_role}'"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
