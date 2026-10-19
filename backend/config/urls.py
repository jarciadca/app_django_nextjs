"""
Rutas URL raíz del proyecto.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Panel de administración.
    path("admin/", admin.site.urls),
    # Rutas del módulo shared (health check).
    path("api/", include("shared.infrastructure.urls")),
    # Aquí se añadirán las rutas de cada feature en fases siguientes.
    # Autenticación de usuarios.
    path("api/auth/", include("features.usuarios.infrastructure.urls")),
]
