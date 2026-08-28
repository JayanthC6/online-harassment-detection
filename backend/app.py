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

app = Flask(__name__)
CORS(app)  # allow the React dev server to call this API

# Bind limiter to app after app is created
limiter.init_app(app)

app.register_blueprint(public_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(complaints_bp)

@app.errorhandler(404)
def not_found(e):
    from flask import jsonify, request
    if request.path.startswith('/api/') or request.path.startswith('/demo/') or request.accept_mimetypes.accept_json:
        return jsonify(error="Not found"), 404
    return jsonify(error="Not found"), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)