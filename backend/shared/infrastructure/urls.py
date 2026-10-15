"""
Rutas del módulo `shared`.
"""

from django.urls import path

from .views import HealthCheckView

# Namespace para reverse("shared:health").
app_name = "shared"

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
]
