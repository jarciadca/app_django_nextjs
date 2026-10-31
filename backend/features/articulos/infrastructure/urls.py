"""
Rutas URL del slice `articulos` (Fase 4c.1).

Endpoints:
    /                    → GET (lista), POST (crear)
    /<uuid>/             → GET (detalle), PUT (actualizar), DELETE (eliminar)

En Fase 4c.2 se añadirán:
    /<uuid>/autores/     → GET, PUT
En Fase 4c.3 se añadirán:
    /<uuid>/categorias/  → GET, PUT
    /<uuid>/publicar/    → POST
    /<uuid>/despublicar/ → POST
"""

from django.urls import path

from features.articulos.infrastructure.views import (
    ArticuloDetailView,
    ArticulosListView,
)

app_name = "articulos"

urlpatterns = [
    # GET  /api/articulos/  → lista
    # POST /api/articulos/  → crear
    path("", ArticulosListView.as_view(), name="lista"),
    # GET    /api/articulos/<uuid>/  → detalle
    # PUT    /api/articulos/<uuid>/  → actualizar
    # DELETE /api/articulos/<uuid>/  → eliminar
    path("<uuid:articulo_id>/", ArticuloDetailView.as_view(), name="detalle"),
]
