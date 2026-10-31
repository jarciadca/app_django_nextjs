"""
Tests de API del slice `articulos` (Fase 4c.1).

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Usa `pytest-django` + `APIClient` para verificar el contrato HTTP
completo contra una BD de test (PostgreSQL temporal).

Cubre:
  - CRUD completo (GET, POST, GET detail, PUT, DELETE).
  - Autenticación JWT (401 sin token).
  - Validaciones (400: título vacío, año fuera de rango, DOI inválido).
  - Conflictos (409: DOI duplicado).
  - Filtros por querystring (?estado=, ?anio=, ?revista=).
  - Paginación (?page=, ?page_size=).
  - 404 en UUID inexistente.
════════════════════════════════════════════════════════════════════
"""

from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from features.revistas.infrastructure.models import Revista
from features.usuarios.infrastructure.models import Usuario


@pytest.fixture
def usuario() -> Usuario:
    """Usuario de test para autenticación."""
    return Usuario.objects.create_user(
        username="test_articulos",
        email="test_articulos@example.com",
        password="password123",
    )


@pytest.fixture
def revista() -> Revista:
    """Revista de test para asociar artículos."""
    return Revista.objects.create(
        nombre="Nature",
        issn="0028-0836",
        editorial="Springer",
        pais="GB",
        sitio_web="https://www.nature.com",
    )


@pytest.fixture
def auth_client(usuario: Usuario) -> APIClient:
    """Cliente DRF autenticado con JWT."""
    client = APIClient()
    r = client.post(
        "/api/auth/login/",
        {"username": usuario.username, "password": "password123"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['access']}")
    return client


# ═══════════════════════════════════════════════════════════════════
# Tests: Autenticación
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
def test_sin_auth_falla_401() -> None:
    """GET /api/articulos/ sin token → 401."""
    client = APIClient()
    r = client.get("/api/articulos/")
    assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════
# Tests: Crear artículo
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
@pytest.mark.integration
def test_crear_articulo_valido(auth_client: APIClient, revista: Revista) -> None:
    """POST /api/articulos/ con datos válidos → 201."""
    r = auth_client.post(
        "/api/articulos/",
        {
            "titulo": "Quantum entanglement",
            "anio": 2024,
            "revista_id": str(revista.id),
            "resumen": "Estudio sobre entrelazamiento.",
            "palabras_clave": "quantum, graphene",
            "doi": "10.1038/nature12345",
            "idioma": "en",
            "estado": "borrador",
        },
        format="json",
    )
    assert r.status_code == 201
    data = r.json()
    assert data["titulo"] == "Quantum entanglement"
    assert data["anio"] == 2024
    assert data["doi"] == "10.1038/nature12345"
    assert data["estado"] == "borrador"
    assert "id" in data


@pytest.mark.django_db
def test_crear_articulo_sin_titulo_falla_400(auth_client: APIClient, revista: Revista) -> None:
    """POST con título vacío → 400."""
    r = auth_client.post(
        "/api/articulos/",
        {"titulo": "", "anio": 2024, "revista_id": str(revista.id)},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_crear_articulo_anio_fuera_de_rango_falla_400(
    auth_client: APIClient, revista: Revista
) -> None:
    """POST con año 3000 → 400 (VO Anio rechaza)."""
    r = auth_client.post(
        "/api/articulos/",
        {
            "titulo": "Futurista",
            "anio": 3000,
            "revista_id": str(revista.id),
        },
        format="json",
    )
    assert r.status_code == 400
    assert r.json()["title"] == "anio_invalid"


@pytest.mark.django_db
def test_crear_articulo_doi_invalido_falla_400(auth_client: APIClient, revista: Revista) -> None:
    """POST con DOI mal formado → 400."""
    r = auth_client.post(
        "/api/articulos/",
        {
            "titulo": "Test",
            "anio": 2024,
            "revista_id": str(revista.id),
            "doi": "abc123",
        },
        format="json",
    )
    assert r.status_code == 400
    assert r.json()["title"] == "doi_invalid"


@pytest.mark.django_db
def test_crear_articulo_doi_duplicado_falla_409(auth_client: APIClient, revista: Revista) -> None:
    """Dos artículos con el mismo DOI → el segundo da 409."""
    payload = {
        "titulo": "A",
        "anio": 2024,
        "revista_id": str(revista.id),
        "doi": "10.1038/nature12345",
    }
    r1 = auth_client.post("/api/articulos/", payload, format="json")
    assert r1.status_code == 201

    payload["titulo"] = "B"
    r2 = auth_client.post("/api/articulos/", payload, format="json")
    assert r2.status_code == 409
    assert r2.json()["title"] == "doi_taken"


# ═══════════════════════════════════════════════════════════════════
# Tests: Listar y filtrar
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
@pytest.mark.integration
def test_listar_articulos(auth_client: APIClient, revista: Revista) -> None:
    """GET /api/articulos/ devuelve lista paginada."""
    for i in range(3):
        auth_client.post(
            "/api/articulos/",
            {
                "titulo": f"Artículo {i}",
                "anio": 2024,
                "revista_id": str(revista.id),
            },
            format="json",
        )

    r = auth_client.get("/api/articulos/")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 3
    assert len(data["results"]) == 3


@pytest.mark.django_db
def test_filtrar_por_estado(auth_client: APIClient, revista: Revista) -> None:
    """?estado=publicado devuelve solo publicados."""
    auth_client.post(
        "/api/articulos/",
        {
            "titulo": "Borrador",
            "anio": 2024,
            "revista_id": str(revista.id),
            "estado": "borrador",
        },
        format="json",
    )
    auth_client.post(
        "/api/articulos/",
        {
            "titulo": "Publicado",
            "anio": 2024,
            "revista_id": str(revista.id),
            "estado": "publicado",
            "fecha_publicacion": "2024-05-01",
        },
        format="json",
    )

    r = auth_client.get("/api/articulos/?estado=publicado")
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["titulo"] == "Publicado"


@pytest.mark.django_db
def test_filtrar_por_anio(auth_client: APIClient, revista: Revista) -> None:
    """?anio=2020 devuelve solo ese año."""
    auth_client.post(
        "/api/articulos/",
        {"titulo": "A", "anio": 2020, "revista_id": str(revista.id)},
        format="json",
    )
    auth_client.post(
        "/api/articulos/",
        {"titulo": "B", "anio": 2024, "revista_id": str(revista.id)},
        format="json",
    )

    r = auth_client.get("/api/articulos/?anio=2020")
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["titulo"] == "A"


@pytest.mark.django_db
def test_filtrar_por_revista(auth_client: APIClient, revista: Revista) -> None:
    """?revista=<uuid> devuelve solo artículos de esa revista."""
    otra_revista = Revista.objects.create(
        nombre="Science", issn="0036-8075", editorial="AAAS", pais="US"
    )
    auth_client.post(
        "/api/articulos/",
        {"titulo": "A", "anio": 2024, "revista_id": str(revista.id)},
        format="json",
    )
    auth_client.post(
        "/api/articulos/",
        {"titulo": "B", "anio": 2024, "revista_id": str(otra_revista.id)},
        format="json",
    )

    r = auth_client.get(f"/api/articulos/?revista={revista.id}")
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert r.json()["results"][0]["titulo"] == "A"


# ═══════════════════════════════════════════════════════════════════
# Tests: Detalle, actualizar, eliminar
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
def test_detalle_articulo(auth_client: APIClient, revista: Revista) -> None:
    """GET /api/articulos/<uuid>/ devuelve el artículo."""
    r = auth_client.post(
        "/api/articulos/",
        {"titulo": "Test", "anio": 2024, "revista_id": str(revista.id)},
        format="json",
    )
    articulo_id = r.json()["id"]

    r = auth_client.get(f"/api/articulos/{articulo_id}/")
    assert r.status_code == 200
    assert r.json()["id"] == articulo_id


@pytest.mark.django_db
def test_detalle_inexistente_falla_404(auth_client: APIClient) -> None:
    """GET con UUID que no existe → 404."""
    r = auth_client.get(f"/api/articulos/{uuid4()}/")
    assert r.status_code == 404
    assert r.json()["title"] == "articulo_not_found"


@pytest.mark.django_db
def test_actualizar_articulo(auth_client: APIClient, revista: Revista) -> None:
    """PUT actualiza título, estado y fecha."""
    r = auth_client.post(
        "/api/articulos/",
        {"titulo": "Original", "anio": 2024, "revista_id": str(revista.id)},
        format="json",
    )
    articulo_id = r.json()["id"]

    r = auth_client.put(
        f"/api/articulos/{articulo_id}/",
        {
            "titulo": "Modificado",
            "anio": 2024,
            "revista_id": str(revista.id),
            "estado": "publicado",
            "fecha_publicacion": "2024-06-15",
        },
        format="json",
    )
    assert r.status_code == 200
    assert r.json()["titulo"] == "Modificado"
    assert r.json()["estado"] == "publicado"


@pytest.mark.django_db
def test_actualizar_inexistente_falla_404(auth_client: APIClient, revista: Revista) -> None:
    """PUT a UUID inexistente → 404."""
    r = auth_client.put(
        f"/api/articulos/{uuid4()}/",
        {"titulo": "X", "anio": 2024, "revista_id": str(revista.id)},
        format="json",
    )
    assert r.status_code == 404


@pytest.mark.django_db
def test_eliminar_articulo(auth_client: APIClient, revista: Revista) -> None:
    """DELETE elimina el artículo → 204."""
    r = auth_client.post(
        "/api/articulos/",
        {"titulo": "Test", "anio": 2024, "revista_id": str(revista.id)},
        format="json",
    )
    articulo_id = r.json()["id"]

    r = auth_client.delete(f"/api/articulos/{articulo_id}/")
    assert r.status_code == 204

    r = auth_client.get(f"/api/articulos/{articulo_id}/")
    assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# Tests: Paginación
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.django_db
def test_page_size_fuera_de_rango_falla_400(
    auth_client: APIClient,
) -> None:
    """?page_size=500 → 400."""
    r = auth_client.get("/api/articulos/?page_size=500")
    assert r.status_code == 400
    assert r.json()["title"] == "page_size_invalid"


@pytest.mark.django_db
def test_paginacion_funciona(auth_client: APIClient, revista: Revista) -> None:
    """?page=2&page_size=2 devuelve la segunda página."""
    for i in range(5):
        auth_client.post(
            "/api/articulos/",
            {
                "titulo": f"Art {i}",
                "anio": 2024,
                "revista_id": str(revista.id),
            },
            format="json",
        )

    r = auth_client.get("/api/articulos/?page=2&page_size=2")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 5
    assert data["page"] == 2
    assert data["page_size"] == 2
    assert len(data["results"]) == 2
