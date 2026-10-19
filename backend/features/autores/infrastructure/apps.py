"""
Configuración de la app Django `autores`.
"""

from django.apps import AppConfig


class AutoresConfig(AppConfig):
    """Configuración de la app autores."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "features.autores.infrastructure"
    label = "autores"
    verbose_name = "Autores"
