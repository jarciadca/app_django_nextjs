"""
Tests de casos de uso de `articulos` con repositorio fake.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Estos tests verifican la LÓGICA DE NEGOCIO sin tocar la BD.
Cubren:
  - Crear artículo válido.
  - Título vacío → ValidationError.
  - Año fuera de rango → ValidationError.
  - DOI con formato inválido → ValidationError.
  - DOI duplicado → ConflictError.
  - Actualizar artículo que no existe → NotFoundError.
  - Actualizar sin cambiar DOI (no debe dar conflicto).
  - Eliminar artículo existente e inexistente.
  - Listar con paginación inválida → ValidationError.

Usan `FakeArticuloRepository` que implementa el Protocol
`ArticuloRepository` con un dict en memoria.
════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from features.articulos.application.dtos import ArticuloInputDTO
from features.articulos.application.use_cases import (
    ActualizarArticuloUseCase,
    CrearArticuloUseCase,
    EliminarArticuloUseCase,
    ListarArticulosUseCase,
    ObtenerArticuloUseCase,
)
from features.articulos.domain.entities import Articulo
from shared.domain.exceptions import ConflictError, NotFoundError, ValidationError


class FakeArticuloRepository:
    """Repositorio en memoria que implementa ArticuloRepository."""

    def __init__(self) -> None:
        self._data: dict[UUID, Articulo] = {}

    def list_all(
        self,
        *,
        search: str | None = None,
        estado: str | None = None,
        revista_id: UUID | None = None,
        anio: int | None = None,
        anio_min: int | None = None,
        anio_max: int | None = None,
        idioma: str | None = None,
        ordering: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Articulo], int]:
        items = list(self._data.values())
        if estado:
            items = [a for a in items if a.estado == estado]
        if revista_id:
            items = [a for a in items if a.revista_id == revista_id]
        if anio is not None:
            items = [a for a in items if a.anio == anio]
        if anio_min is not None:
            items = [a for a in items if a.anio >= anio_min]
        if anio_max is not None:
            items = [a for a in items if a.anio <= anio_max]
        if idioma:
            items = [a for a in items if a.idioma == idioma]
        if search:
            q = search.lower()
            items = [
                a
                for a in items
                if q in a.titulo.lower() or q in a.resumen.lower() or q in a.palabras_clave.lower()
            ]
        total = len(items)
        return items[offset : offset + limit], total

    def get_by_id(self, articulo_id: UUID) -> Articulo | None:
        return self._data.get(articulo_id)

    def exists_by_doi(self, doi: str, exclude_id: UUID | None = None) -> bool:
        for art in self._data.values():
            if art.doi == doi and (exclude_id is None or art.id != exclude_id):
                return True
        return False

    def create(
        self,
        *,
        titulo: str,
        resumen: str,
        palabras_clave: str,
        doi: str | None,
        anio: int,
        idioma: str,
        estado: str,
        fecha_publicacion: date | None,
        revista_id: UUID,
    ) -> Articulo:
        art = Articulo(
            id=uuid4(),
            titulo=titulo,
            resumen=resumen,
            palabras_clave=palabras_clave,
            doi=doi,
            anio=anio,
            idioma=idioma,
            estado=estado,
            fecha_publicacion=fecha_publicacion,
            revista_id=revista_id,
        )
        self._data[art.id] = art
        return art

    def update(
        self,
        articulo_id: UUID,
        *,
        titulo: str | None = None,
        resumen: str | None = None,
        palabras_clave: str | None = None,
        doi: str | None = None,
        anio: int | None = None,
        idioma: str | None = None,
        estado: str | None = None,
        fecha_publicacion: date | None = None,
        revista_id: UUID | None = None,
    ) -> Articulo | None:
        current = self._data.get(articulo_id)
        if current is None:
            return None
        updated = Articulo(
            id=current.id,
            titulo=titulo if titulo is not None else current.titulo,
            resumen=resumen if resumen is not None else current.resumen,
            palabras_clave=(
                palabras_clave if palabras_clave is not None else current.palabras_clave
            ),
            doi=doi if doi is not None else current.doi,
            anio=anio if anio is not None else current.anio,
            idioma=idioma if idioma is not None else current.idioma,
            estado=estado if estado is not None else current.estado,
            fecha_publicacion=(
                fecha_publicacion if fecha_publicacion is not None else current.fecha_publicacion
            ),
            revista_id=revista_id if revista_id is not None else current.revista_id,
        )
        self._data[articulo_id] = updated
        return updated

    def delete(self, articulo_id: UUID) -> bool:
        return self._data.pop(articulo_id, None) is not None


# ═══════════════════════════════════════════════════════════════════
# Helper para construir DTOs rápidamente
# ═══════════════════════════════════════════════════════════════════
def _make_dto(
    *,
    titulo: str = "Quantum entanglement",
    anio: int = 2024,
    revista_id: UUID | None = None,
    resumen: str = "",
    palabras_clave: str = "",
    doi: str | None = None,
    idioma: str = "es",
    estado: str = "borrador",
    fecha_publicacion: date | None = None,
) -> ArticuloInputDTO:
    """Construye un DTO válido para tests, permitiendo overrides."""
    return ArticuloInputDTO(
        titulo=titulo,
        anio=anio,
        revista_id=revista_id if revista_id is not None else uuid4(),
        resumen=resumen,
        palabras_clave=palabras_clave,
        doi=doi,
        idioma=idioma,
        estado=estado,
        fecha_publicacion=fecha_publicacion,
    )


# ═══════════════════════════════════════════════════════════════════
# Tests: Crear
# ═══════════════════════════════════════════════════════════════════
def test_crear_articulo_valido() -> None:
    repo = FakeArticuloRepository()
    out = CrearArticuloUseCase(repo).execute(
        _make_dto(titulo="Entrelazamiento cuántico", anio=2024)
    )
    assert out.titulo == "Entrelazamiento cuántico"
    assert out.anio == 2024
    assert out.estado == "borrador"


def test_crear_articulo_titulo_vacio_falla() -> None:
    repo = FakeArticuloRepository()
    with pytest.raises(ValidationError) as exc_info:
        CrearArticuloUseCase(repo).execute(_make_dto(titulo=""))
    assert exc_info.value.code == "titulo_empty"


def test_crear_articulo_anio_fuera_de_rango_falla() -> None:
    repo = FakeArticuloRepository()
    with pytest.raises(ValidationError) as exc_info:
        CrearArticuloUseCase(repo).execute(_make_dto(anio=3000))
    assert exc_info.value.code == "anio_invalid"


def test_crear_articulo_doi_invalido_falla() -> None:
    repo = FakeArticuloRepository()
    with pytest.raises(ValidationError) as exc_info:
        CrearArticuloUseCase(repo).execute(_make_dto(doi="abc123"))
    assert exc_info.value.code == "doi_invalid"


def test_crear_articulo_doi_duplicado_falla() -> None:
    repo = FakeArticuloRepository()
    CrearArticuloUseCase(repo).execute(_make_dto(doi="10.1038/nature12345"))

    with pytest.raises(ConflictError) as exc_info:
        CrearArticuloUseCase(repo).execute(_make_dto(titulo="Otro", doi="10.1038/nature12345"))
    assert exc_info.value.code == "doi_taken"


def test_crear_articulo_sin_doi_permite_duplicados() -> None:
    """Dos artículos sin DOI deben poder coexistir (None != None en SQL)."""
    repo = FakeArticuloRepository()
    CrearArticuloUseCase(repo).execute(_make_dto(titulo="A", doi=None))
    # El segundo también sin DOI. No debe fallar.
    CrearArticuloUseCase(repo).execute(_make_dto(titulo="B", doi=None))
    items, total = ListarArticulosUseCase(repo).execute()
    assert total == 2


# ═══════════════════════════════════════════════════════════════════
# Tests: Obtener
# ═══════════════════════════════════════════════════════════════════
def test_obtener_articulo_existente() -> None:
    repo = FakeArticuloRepository()
    creado = CrearArticuloUseCase(repo).execute(_make_dto(titulo="Test"))
    out = ObtenerArticuloUseCase(repo).execute(creado.id)
    assert out.titulo == "Test"


def test_obtener_articulo_inexistente_falla() -> None:
    repo = FakeArticuloRepository()
    with pytest.raises(NotFoundError) as exc_info:
        ObtenerArticuloUseCase(repo).execute(uuid4())
    assert exc_info.value.code == "articulo_not_found"


# ═══════════════════════════════════════════════════════════════════
# Tests: Actualizar
# ═══════════════════════════════════════════════════════════════════
def test_actualizar_articulo_cambia_campos() -> None:
    repo = FakeArticuloRepository()
    creado = CrearArticuloUseCase(repo).execute(_make_dto(titulo="Original", anio=2020))

    out = ActualizarArticuloUseCase(repo).execute(
        creado.id, _make_dto(titulo="Modificado", anio=2024)
    )
    assert out.titulo == "Modificado"
    assert out.anio == 2024


def test_actualizar_articulo_sin_cambiar_doi_no_falla() -> None:
    """Si el DOI no cambia, no debe dar conflicto."""
    repo = FakeArticuloRepository()
    creado = CrearArticuloUseCase(repo).execute(_make_dto(titulo="A", doi="10.1038/nature12345"))
    # Actualizamos cambiando título pero manteniendo el mismo DOI.
    out = ActualizarArticuloUseCase(repo).execute(
        creado.id,
        _make_dto(titulo="A modificado", doi="10.1038/nature12345"),
    )
    assert out.titulo == "A modificado"


def test_actualizar_articulo_con_doi_de_otro_falla() -> None:
    repo = FakeArticuloRepository()
    CrearArticuloUseCase(repo).execute(_make_dto(titulo="A", doi="10.1038/nature11111"))
    b = CrearArticuloUseCase(repo).execute(_make_dto(titulo="B", doi=None))

    with pytest.raises(ConflictError) as exc_info:
        ActualizarArticuloUseCase(repo).execute(
            b.id, _make_dto(titulo="B", doi="10.1038/nature11111")
        )
    assert exc_info.value.code == "doi_taken"


def test_actualizar_articulo_inexistente_falla() -> None:
    repo = FakeArticuloRepository()
    with pytest.raises(NotFoundError):
        ActualizarArticuloUseCase(repo).execute(uuid4(), _make_dto())


# ═══════════════════════════════════════════════════════════════════
# Tests: Eliminar
# ═══════════════════════════════════════════════════════════════════
def test_eliminar_articulo_existente() -> None:
    repo = FakeArticuloRepository()
    creado = CrearArticuloUseCase(repo).execute(_make_dto())
    EliminarArticuloUseCase(repo).execute(creado.id)
    # Verificar que ya no existe
    with pytest.raises(NotFoundError):
        ObtenerArticuloUseCase(repo).execute(creado.id)


def test_eliminar_articulo_inexistente_falla() -> None:
    repo = FakeArticuloRepository()
    with pytest.raises(NotFoundError):
        EliminarArticuloUseCase(repo).execute(uuid4())


# ═══════════════════════════════════════════════════════════════════
# Tests: Listar
# ═══════════════════════════════════════════════════════════════════
def test_listar_paginacion_invalida_falla() -> None:
    repo = FakeArticuloRepository()
    use_case = ListarArticulosUseCase(repo)

    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(page=0)
    assert exc_info.value.code == "page_invalid"

    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(page_size=500)
    assert exc_info.value.code == "page_size_invalid"


def test_listar_filtra_por_estado() -> None:
    repo = FakeArticuloRepository()
    CrearArticuloUseCase(repo).execute(_make_dto(titulo="A", estado="borrador"))
    CrearArticuloUseCase(repo).execute(_make_dto(titulo="B", estado="publicado"))

    items, total = ListarArticulosUseCase(repo).execute(estado="publicado")
    assert total == 1
    assert items[0].titulo == "B"
