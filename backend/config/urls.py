"""
Rutas URL raíz del proyecto.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# Tipo anotado para que mypy no se queje al concatenar listas heterogéneas.
urlpatterns = [
    # Panel de administración.
    path("admin/", admin.site.urls),
    # Health check.
    path("api/", include("shared.infrastructure.urls")),
    # Autenticación.
    path("api/auth/", include("features.usuarios.infrastructure.urls")),
    # Autores.
    path("api/autores/", include("features.autores.infrastructure.urls")),
    # Revistas (Fase 4b).
    # API: expone /api/revistas/ y /api/revistas/<uuid>/.
    path("api/revistas/", include("features.revistas.infrastructure.urls")),
    # Categorías.
    path("api/categorias/", include("features.categorias.infrastructure.urls")),
    # Artículos (Fase 4c.1).
    path("api/articulos/", include("features.articulos.infrastructure.urls")),
]

# En desarrollo servimos los archivos media (fotos de autores).
if settings.DEBUG:
    # `+=` con listas de distintos tipos molesta a mypy; lo hacemos explícito.
    urlpatterns = [*urlpatterns, *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)]  # type: ignore[list-item]
