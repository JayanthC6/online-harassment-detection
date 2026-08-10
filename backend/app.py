"""
Flask backend for the Online Harassment Detection System.

Refactored to use API blueprints.
"""
import os
import sys

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

from api.routes_public import public_bp
from api.routes_admin import admin_bp

app = Flask(__name__)
CORS(app)  # allow the React dev server to call this API

app.register_blueprint(public_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)