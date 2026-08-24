"""
Shared Flask-Limiter instance.

Defined in its own module to avoid the circular import that would occur
if routes_public.py imported directly from app.py while app.py imports
the blueprints from routes_public.py.

Usage:
    from extensions import limiter   # in routes or app
    limiter.init_app(app)            # in app.py
"""
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],          # no global default — limits applied per-route only
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)
