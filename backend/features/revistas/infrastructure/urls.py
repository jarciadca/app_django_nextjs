"""
Rutas URL del slice `revistas`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Este archivo mapea URLs HTTP a vistas. Cada entrada `path(...)` es
un endpoint REST:

    path("", RevistasListView.as_view())          → /api/revistas/
    path("<uuid:revista_id>/", RevistaDetailView) → /api/revistas/<uuid>/

El prefijo `/api/revistas/` NO está aquí: se define en `config/urls.py`
con `path("api/revistas/", include("features.revistas.infrastructure.urls"))`.
Así, si mañana cambias `/api/` por `/v1/`, solo tocas `config/urls.py`.

`<uuid:revista_id>` es un converter de Django:
    - Solo acepta strings con formato UUID.
    - Si llega un string no-UUID → 404 automático (antes de la vista).
    - Se pasa al método de la vista como `revista_id: UUID`.
════════════════════════════════════════════════════════════════════
"""

# `path` de django.urls para definir rutas simples.
from django.urls import path

# Importamos las vistas del slice.
from features.revistas.infrastructure.views import (
    RevistaDetailView,
    RevistasListView,
)

# `app_name` permite namespacing en reverse(): reverse("revistas:lista").
app_name = "revistas"

urlpatterns = [
    # GET  /api/revistas/  → listar (con paginación y búsqueda)
    # POST /api/revistas/  → crear
    path("", RevistasListView.as_view(), name="lista"),
    # GET    /api/revistas/<uuid>/  → detalle
    # PUT    /api/revistas/<uuid>/  → actualizar
    # DELETE /api/revistas/<uuid>/  → eliminar
    path("<uuid:revista_id>/", RevistaDetailView.as_view(), name="detalle"),
]
