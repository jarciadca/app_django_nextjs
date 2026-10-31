"""Configuración de la app Django `articulos`."""

from django.apps import AppConfig


class ArticulosConfig(AppConfig):
    """Configuración de la app articulos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "features.articulos.infrastructure"
    label = "articulos"
    verbose_name = "Artículos"
