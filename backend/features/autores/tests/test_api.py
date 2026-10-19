"""
Tests de API del slice `autores`.
"""

import pytest
from rest_framework.test import APIClient

from features.usuarios.infrastructure.models import Usuario


@pytest.fixture
def auth_client() -> APIClient:
    """Cliente autenticado con JWT."""
    Usuario.objects.create_user(username="test", email="test@example.com", password="password123")
    client = APIClient()
    r = client.post(
        "/api/auth/login/",
        {"username": "test", "password": "password123"},
        format="json",
    )
    access = r.json()["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


@pytest.mark.django_db
@pytest.mark.integration
def test_crud_autor(auth_client: APIClient) -> None:
    # Crear
    r = auth_client.post(
        "/api/autores/",
        {
            "nombre": "Ada",
            "apellido": "Lovelace",
            "email": "ada@example.com",
            "afiliacion": "UAM",
        },
        format="json",
    )
    assert r.status_code == 201
    autor_id = r.json()["id"]

    # Listar
    r = auth_client.get("/api/autores/")
    assert r.status_code == 200
    assert r.json()["count"] == 1

    # Obtener
    r = auth_client.get(f"/api/autores/{autor_id}/")
    assert r.status_code == 200
    assert r.json()["nombre"] == "Ada"

    # Actualizar
    r = auth_client.put(
        f"/api/autores/{autor_id}/",
        {
            "nombre": "Ada",
            "apellido": "Lovelace",
            "email": "ada@example.com",
            "afiliacion": "Oxford",
        },
        format="json",
    )
    assert r.status_code == 200
    assert r.json()["afiliacion"] == "Oxford"

    # Eliminar
    r = auth_client.delete(f"/api/autores/{autor_id}/")
    assert r.status_code == 204


@pytest.mark.django_db
def test_autores_requiere_auth() -> None:
    client = APIClient()
    r = client.get("/api/autores/")
    assert r.status_code == 401
