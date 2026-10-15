"""
Settings para desarrollo local.
"""

# Hereda todo de base.py.
from .base import *  # noqa: F403

# Debug activo en local.
DEBUG = True

# CORS: permitimos el frontend de Next.js.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Emails en consola (no se envían realmente).
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
