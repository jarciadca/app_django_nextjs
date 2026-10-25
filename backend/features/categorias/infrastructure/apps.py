"""
Configuración de la app Django `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Esta AppConfig hace que Django:
  1. Importe `models.py` → registra el modelo `Categoria`.
  2. Reconozca la app para `makemigrations categorias`.
  3. Habilite `manage.py` sobre ella.

API: sin esta configuración en `INSTALLED_APPS`, la API no encontraría
el modelo `Categoria` y fallaría al usarlo.
════════════════════════════════════════════════════════════════════
"""

# `AppConfig` es la clase base de Django para apps.
from django.apps import AppConfig


class CategoriasConfig(AppConfig):
    """Configuración de la app categorias."""

    default_auto_field = "django.db.models.BigAutoField"

    # Ruta Python de la app (dónde está models.py).
    name = "features.categorias.infrastructure"

    # `label` corto, usado en migraciones, FKs, etc.
    # Gracias a esto, AUTH_USER_MODEL y futuras referencias como
    # `ForeignKey("categorias.Categoria")` funcionan con nombre corto.
    label = "categorias"

    # Nombre legible en el admin de Django.
    verbose_name = "Categorías"
