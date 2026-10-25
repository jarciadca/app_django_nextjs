"""
Tests de API del slice `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Estos tests usan la BD de test (pytest-django) y el cliente DRF para
verificar el contrato HTTP completo: status codes, JSON, jerarquía,
detección de ciclos, PROTECT, auth.
════════════════════════════════════════════════════════════════════
"""

import pytest
from rest_framework.test import APIClient

from features.usuarios.infrastructure.models import Usuario


@pytest.fixture
def auth_client() -> APIClient:
    """Cliente DRF autenticado con JWT."""
    Usuario.objects.create_user(
        username="test_cat", email="test_cat@example.com", password="password123"
    )
    client = APIClient()
    r = client.post(
        "/api/auth/login/",
        {"username": "test_cat", "password": "password123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['access']}")
    return client


# ═══════════════════════════════════════════════════════════════════
# Tests básicos de CRUD
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
@pytest.mark.integration
def test_crear_categoria_raiz(auth_client: APIClient) -> None:
    r = auth_client.post(
        "/api/categorias/",
        {"nombre": "Ciencias", "descripcion": "..."},
        format="json",
    )
    assert r.status_code == 201
    data = r.json()
    assert data["nombre"] == "Ciencias"
    assert data["parent_id"] is None


@pytest.mark.django_db
@pytest.mark.integration
def test_listar_categorias(auth_client: APIClient) -> None:
    auth_client.post("/api/categorias/", {"nombre": "A"}, format="json")
    auth_client.post("/api/categorias/", {"nombre": "B"}, format="json")

    r = auth_client.get("/api/categorias/")
    assert r.status_code == 200
    assert r.json()["count"] == 2


@pytest.mark.django_db
@pytest.mark.integration
def test_jerarquia_completa(auth_client: APIClient) -> None:
    """Crear Ciencias → Física → Mecánica y verificar subcategorías."""
    ciencias_id = auth_client.post(
        "/api/categorias/", {"nombre": "Ciencias"}, format="json"
    ).json()["id"]
    fisica_id = auth_client.post(
        "/api/categorias/",
        {"nombre": "Física", "parent_id": ciencias_id},
        format="json",
    ).json()["id"]
    auth_client.post(
        "/api/categorias/",
        {"nombre": "Mecánica", "parent_id": fisica_id},
        format="json",
    )

    # only_roots: solo Ciencias
    r = auth_client.get("/api/categorias/?only_roots=true")
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["nombre"] == "Ciencias"

    # Subcategorías de Ciencias: solo Física
    r = auth_client.get(f"/api/categorias/{ciencias_id}/subcategorias/")
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["nombre"] == "Física"


# ═══════════════════════════════════════════════════════════════════
# Detección de ciclos
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
@pytest.mark.integration
def test_actualizar_creando_ciclo_falla_400(auth_client: APIClient) -> None:
    ciencias_id = auth_client.post(
        "/api/categorias/", {"nombre": "Ciencias"}, format="json"
    ).json()["id"]
    fisica_id = auth_client.post(
        "/api/categorias/",
        {"nombre": "Física", "parent_id": ciencias_id},
        format="json",
    ).json()["id"]
    mecanica_id = auth_client.post(
        "/api/categorias/",
        {"nombre": "Mecánica", "parent_id": fisica_id},
        format="json",
    ).json()["id"]

    # Ciencias → Mecánica (ciclo)
    r = auth_client.put(
        f"/api/categorias/{ciencias_id}/",
        {"nombre": "Ciencias", "parent_id": mecanica_id},
        format="json",
    )
    assert r.status_code == 400
    assert r.json()["title"] == "categoria_ciclo"


# ═══════════════════════════════════════════════════════════════════
# PROTECT
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
@pytest.mark.integration
def test_borrar_categoria_con_hijos_falla_409(auth_client: APIClient) -> None:
    ciencias_id = auth_client.post(
        "/api/categorias/", {"nombre": "Ciencias"}, format="json"
    ).json()["id"]
    auth_client.post(
        "/api/categorias/",
        {"nombre": "Física", "parent_id": ciencias_id},
        format="json",
    )

    r = auth_client.delete(f"/api/categorias/{ciencias_id}/")
    assert r.status_code == 409
    assert r.json()["title"] == "categoria_con_hijos"


# ═══════════════════════════════════════════════════════════════════
# Errores de entrada
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
def test_crear_sin_nombre_falla_400(auth_client: APIClient) -> None:
    r = auth_client.post("/api/categorias/", {"nombre": ""}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_crear_con_parent_inexistente_falla_404(auth_client: APIClient) -> None:
    r = auth_client.post(
        "/api/categorias/",
        {
            "nombre": "Huérfana",
            "parent_id": "00000000-0000-0000-0000-000000000000",
        },
        format="json",
    )
    assert r.status_code == 404
    assert r.json()["title"] == "parent_not_found"


@pytest.mark.django_db
def test_sin_auth_falla_401() -> None:
    client = APIClient()
    r = client.get("/api/categorias/")
    assert r.status_code == 401


@pytest.mark.django_db
def test_page_size_fuera_de_rango_falla_400(auth_client: APIClient) -> None:
    r = auth_client.get("/api/categorias/?page_size=500")
    assert r.status_code == 400
    assert r.json()["title"] == "page_size_invalid"
