"""
Settings para tests (pytest, CI).
"""

from .base import *  # noqa: F403

DEBUG = False

# Hasher rápido: en tests no importa la seguridad, solo la velocidad.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Emails en memoria: los tests pueden inspeccionarlos.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
