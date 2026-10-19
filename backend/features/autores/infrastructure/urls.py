"""
Rutas URL del slice `autores`.
"""

from django.urls import path

from features.autores.infrastructure.views import (
    AutorDetailView,
    AutoresListView,
)

app_name = "autores"

urlpatterns = [
    path("", AutoresListView.as_view(), name="lista"),
    path("<uuid:autor_id>/", AutorDetailView.as_view(), name="detalle"),
]
