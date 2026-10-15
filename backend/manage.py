#!/usr/bin/env python
"""
Punto de entrada CLI de Django.
"""

# `os` para manejar variables de entorno.
import os

# `sys` para acceder a sys.argv y al path.
import sys


def main() -> None:
    """Ejecuta tareas administrativas de Django."""

    # Settings por defecto si el usuario no los ha fijado ya.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    try:
        # Import tardío para que el error sea claro si Django no está instalado.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Error amigable si el venv no está activo o falta instalar dependencias.
        raise ImportError(
            "No se pudo importar Django. ¿Está el venv activado y las "
            "dependencias instaladas con `pip install -r requirements/local.txt`?"
        ) from exc

    # Ejecuta el comando pasado por CLI (runserver, migrate, ...).
    execute_from_command_line(sys.argv)


# Solo se ejecuta si invocamos el archivo directamente.
if __name__ == "__main__":
    main()
