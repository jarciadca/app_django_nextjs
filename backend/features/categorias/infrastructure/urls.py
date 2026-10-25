"""
Rutas URL del slice `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Mapea URLs HTTP a vistas. El prefijo `/api/categorias/` se define en
`config/urls.py`; aquí solo las rutas relativas.

Endpoints:
    /                                    → lista + create
    /<uuid>/                             → detail + update + delete
    /<uuid>/subcategorias/               → hijos directos (endpoint extra)

`<uuid:categoria_id>` es un converter de Django: solo acepta UUIDs.
Si llega algo que no es UUID → 404 antes de ejecutar la vista.
════════════════════════════════════════════════════════════════════
"""

from django.urls import path

from features.categorias.infrastructure.views import (
    CategoriaDetailView,
    CategoriasListView,
    CategoriaSubcategoriasView,
)

app_name = "categorias"

urlpatterns = [
    # GET  /api/categorias/  → lista
    # POST /api/categorias/  → crear
    path("", CategoriasListView.as_view(), name="lista"),
    # GET    /api/categorias/<uuid>/subcategorias/  → hijos directos
    # IMPORTANTE: esta ruta va ANTES de "<uuid:...>/" para que Django
    # no interprete "subcategorias" como un UUID (que no lo es).
    path(
        "<uuid:categoria_id>/subcategorias/",
        CategoriaSubcategoriasView.as_view(),
        name="subcategorias",
    ),
    # GET    /api/categorias/<uuid>/  → detalle
    # PUT    /api/categorias/<uuid>/  → actualizar
    # DELETE /api/categorias/<uuid>/  → eliminar
    path("<uuid:categoria_id>/", CategoriaDetailView.as_view(), name="detalle"),
]
