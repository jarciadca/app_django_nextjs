"""
Test de humo del endpoint /api/health/.
"""

# `pytest` para fixtures y marcadores.
import pytest

# `APIClient` de DRF para hacer requests sin levantar servidor.
from rest_framework.test import APIClient


# Marcamos como test de integración (toca URLs y settings reales).
@pytest.mark.integration
def test_health_check_devuelve_ok() -> None:
    """GET /api/health/ debe devolver 200 con {"status": "ok"}."""
    # Cliente de DRF.
    client = APIClient()
    # Hacemos la petición.
    response = client.get("/api/health/")
    # Verificamos código HTTP.
    assert response.status_code == 200
    # Verificamos el cuerpo JSON.
    assert response.json() == {"status": "ok"}
