"""
Configuración de la app Django `revistas`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Cada app Django necesita una AppConfig para ser descubierta por Django.
Al registrarla en `INSTALLED_APPS`, Django:
  1. Importa `models.py` → registra el modelo `Revista`.
  2. Sabe que existe la app para `makemigrations revistas`.
  3. Habilita los comandos `manage.py` sobre ella.

API: sin esta AppConfig registrada, la API no encontraría el modelo
Revista → el repositorio Django fallaría al consultarlo.
════════════════════════════════════════════════════════════════════
"""

# `AppConfig` es la clase base de Django para configurar apps.
from django.apps import AppConfig


class RevistasConfig(AppConfig):
    """
    Configuración de la app Django `revistas`.

    Django, al arrancar, recorre `INSTALLED_APPS` y por cada entrada
    busca su AppConfig. Aquí le decimos qué nombre usar.
    """

    # `default_auto_field`: tipo de campo para PKs automáticas.
    # No afecta a Revista (que tiene UUID explícito), pero Django lo
    # pide porque es buena práctica fijarlo.
    default_auto_field = "django.db.models.BigAutoField"

    # `name`: ruta Python de la app (dónde vive `models.py`).
    # API: es la ruta interna, no aparece en URLs ni en el JSON.
    name = "features.revistas.infrastructure"

    # `label`: nombre corto. Se usa en:
    #   - `AUTH_USER_MODEL` (no aplica aquí, pero igual)
    #   - Migraciones: `manage.py makemigrations revistas`
    #   - Referencias de FK: `ForeignKey("revistas.Revista")` (Fase 4c)
    # Sin `label`, Django derivaría "infrastructure" del último segmento
    # de `name`, y las migraciones se llamarían `infrastructure_0001_...`.
    label = "revistas"

    # `verbose_name`: nombre legible en el panel admin.
    verbose_name = "Revistas"
