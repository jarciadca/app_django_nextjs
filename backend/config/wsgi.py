"""
Punto de entrada WSGI para producción (gunicorn, uWSGI).
"""

import os

from django.core.wsgi import get_wsgi_application

# En producción se sobreescribe con config.settings.production.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

application = get_wsgi_application()
