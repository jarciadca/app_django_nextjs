"""
Configuración de la app Django `usuarios`.

Django necesita una AppConfig para cada app en INSTALLED_APPS.
Aquí le damos un nombre legible en el admin y evitamos conflictos.
"""

from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    """Configuración de la app usuarios."""

    # Tipo de PK por defecto (BigAutoField) para no heredar warnings.
    default_auto_field = "django.db.models.BigAutoField"

    # Ruta Python de la app. Importante: debe coincidir con dónde está models.py.
    name = "features.usuarios.infrastructure"

    # Label corto que Django usará en AUTH_USER_MODEL, FK "usuarios.Usuario", etc.
    # Sin esto, Django derivaría "infrastructure" del último segmento de `name`,
    # y AUTH_USER_MODEL = "usuarios.Usuario" fallaría.
    label = "usuarios"

    # Nombre legible que se muestra en el admin.
    verbose_name = "Usuarios"
