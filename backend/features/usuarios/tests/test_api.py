"""
Tests de API end-to-end (con BD de test).
"""

import pytest
from rest_framework.test import APIClient

from features.usuarios.infrastructure.models import Usuario


@pytest.mark.django_db
@pytest.mark.integration
def test_flujo_completo_registro_login_me_logout() -> None:
    """Registro → login → /me → logout."""
    client = APIClient()

    # 1. Registro.
    r = client.post(
        "/api/auth/registro/",
        {"username": "pedro", "email": "pedro@example.com", "password": "password123"},
        format="json",
    )
    assert r.status_code == 201
    assert r.json()["username"] == "pedro"

    # 2. Login.
    r = client.post(
        "/api/auth/login/",
        {"username": "pedro", "password": "password123"},
        format="json",
    )
    assert r.status_code == 200
    access = r.json()["access"]
    # La cookie httpOnly debe venir seteada.
    assert "refresh_token" in r.cookies

    # 3. /me con access.
    r = client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {access}")
    assert r.status_code == 200
    assert r.json()["username"] == "pedro"

    # 4. /me sin access → 401.
    r = client.get("/api/auth/me/")
    assert r.status_code == 401

    # 5. Logout.
    r = client.post("/api/auth/logout/")
    assert r.status_code == 204


@pytest.mark.django_db
@pytest.mark.integration
def test_login_falla_con_password_incorrecta() -> None:
    Usuario.objects.create_user(username="pedro", email="pedro@example.com", password="password123")
    client = APIClient()
    r = client.post(
        "/api/auth/login/",
        {"username": "pedro", "password": "otra"},
        format="json",
    )
    assert r.status_code == 401
