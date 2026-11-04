"""
Flask backend for the Online Harassment Detection System.

Refactored to use API blueprints.
"""
import os

# Import torch first on Windows to avoid DLL conflicts with other libraries
try:
    import torch
except Exception as e:
    import logging
    logging.warning(f"Failed to pre-import torch (this is usually fine if torch isn't needed): {e}")

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()  # reads MONGODB_URI from a .env file if present

# Import the shared limiter BEFORE blueprints so the singleton exists
from extensions import limiter

from api.routes_public import public_bp
from api.routes_admin import admin_bp
from api.routes_complaints import complaints_bp
from api.routes_auth import auth_bp

import re

app = Flask(__name__)

# Dev passwords and open CORS must work ONLY when APP_ENV=development.
# In any other environment, restrict CORS to an allowlist plus chrome-extension origins.
app_env = os.environ.get("APP_ENV", "development").lower()
if app_env == "development":
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
else:
    allowed_origins = [
        o.strip() for o in os.environ.get(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173"
        ).split(",") if o.strip()
    ]
    cors_origins = allowed_origins + [re.compile(r"^chrome-extension://[a-z0-9]+$")]
    CORS(app, resources={r"/*": {"origins": cors_origins}}, supports_credentials=True)

# Bind limiter to app after app is created
limiter.init_app(app)

# Register both root-level and /api-prefixed routes to eliminate frontend/backend proxy mismatches
app.register_blueprint(public_bp)
app.register_blueprint(public_bp, name="public_api", url_prefix="/api")
app.register_blueprint(admin_bp)
app.register_blueprint(admin_bp, name="admin_api", url_prefix="/api")
app.register_blueprint(complaints_bp)
app.register_blueprint(complaints_bp, name="complaints_api", url_prefix="/api")
app.register_blueprint(auth_bp)
app.register_blueprint(auth_bp, name="auth_api", url_prefix="/api")

@app.errorhandler(404)
def not_found(e):
    from flask import jsonify, request
    if request.path.startswith('/api/') or request.path.startswith('/demo/') or request.accept_mimetypes.accept_json:
        return jsonify(error="Not found"), 404
    return jsonify(error="Not found"), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)