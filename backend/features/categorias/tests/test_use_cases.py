"""
Tests de casos de uso de `categorias` con repositorio fake.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Estos tests verifican la LÓGICA DE NEGOCIO de los use cases sin tocar
la BD. Son rápidos (milisegundos) y cubren casos que serían difíciles
de provocar en integración:
  - Ciclo al actualizar parent.
  - Parent inexistente al crear.
  - Nombre vacío.
  - Borrado con hijos (simulado con ProtectedError).
════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from django.db.models import ProtectedError

from features.categorias.application.dtos import CategoriaInputDTO
from features.categorias.application.use_cases import (
    ActualizarCategoriaUseCase,
    CrearCategoriaUseCase,
    EliminarCategoriaUseCase,
    ListarSubcategoriasUseCase,
    ObtenerCategoriaUseCase,
)
from features.categorias.domain.entities import Categoria
from shared.domain.exceptions import ConflictError, NotFoundError, ValidationError


class FakeCategoriaRepository:
    """Repositorio en memoria que implementa CategoriaRepository."""

    def __init__(self) -> None:
        self._data: dict[UUID, Categoria] = {}
        self._protect_on_delete: set[UUID] = set()  # ids con hijos (para simular PROTECT)

    def list_all(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        parent_id: UUID | None = None,
        only_roots: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Categoria], int]:
        items = list(self._data.values())
        if parent_id is not None:
            items = [c for c in items if c.parent_id == parent_id]
        elif only_roots:
            items = [c for c in items if c.parent_id is None]
        if search:
            items = [
                c
                for c in items
                if search.lower() in c.nombre.lower()
                or (c.descripcion and search.lower() in c.descripcion.lower())
            ]
        total = len(items)
        return items[offset : offset + limit], total

    def get_by_id(self, categoria_id: UUID) -> Categoria | None:
        return self._data.get(categoria_id)

    def list_children(self, parent_id: UUID) -> list[Categoria]:
        return [c for c in self._data.values() if c.parent_id == parent_id]

    def create(
        self,
        *,
        nombre: str,
        parent_id: UUID | None,
        descripcion: str | None,
    ) -> Categoria:
        cat = Categoria(
            id=uuid4(),
            nombre=nombre,
            parent_id=parent_id,
            descripcion=descripcion,
        )
        self._data[cat.id] = cat
        return cat

    def update(
        self,
        categoria_id: UUID,
        *,
        nombre: str | None = None,
        parent_id: UUID | None = None,
        change_parent: bool = False,
        descripcion: str | None = None,
    ) -> Categoria | None:
        current = self._data.get(categoria_id)
        if current is None:
            return None
        updated = Categoria(
            id=current.id,
            nombre=nombre if nombre is not None else current.nombre,
            parent_id=parent_id if change_parent else current.parent_id,
            descripcion=descripcion if descripcion is not None else current.descripcion,
        )
        self._data[categoria_id] = updated
        return updated

    def delete(self, categoria_id: UUID) -> bool:
        if categoria_id in self._protect_on_delete:
            raise ProtectedError("Categoría con hijos", set())
        return self._data.pop(categoria_id, None) is not None

    def get_ancestor_ids(self, categoria_id: UUID) -> list[UUID]:
        ancestors: list[UUID] = []
        current = self._data.get(categoria_id)
        guard = 0
        while current is not None and current.parent_id is not None and guard < 100:
            ancestors.append(current.parent_id)
            current = self._data.get(current.parent_id)
            guard += 1
        return ancestors


# ═══════════════════════════════════════════════════════════════════
# Tests de Crear
# ═══════════════════════════════════════════════════════════════════
def test_crear_categoria_raiz() -> None:
    repo = FakeCategoriaRepository()
    out = CrearCategoriaUseCase(repo).execute(
        CategoriaInputDTO(nombre="Ciencias", parent_id=None, descripcion="Ciencias naturales")
    )
    assert out.nombre == "Ciencias"
    assert out.parent_id is None


def test_crear_categoria_con_padre_inexistente_falla() -> None:
    repo = FakeCategoriaRepository()
    with pytest.raises(NotFoundError) as exc_info:
        CrearCategoriaUseCase(repo).execute(
            CategoriaInputDTO(nombre="Física", parent_id=uuid4(), descripcion=None)
        )
    assert exc_info.value.code == "parent_not_found"


def test_crear_categoria_nombre_vacio_falla() -> None:
    repo = FakeCategoriaRepository()
    with pytest.raises(ValidationError) as exc_info:
        CrearCategoriaUseCase(repo).execute(
            CategoriaInputDTO(nombre="", parent_id=None, descripcion=None)
        )
    assert exc_info.value.code == "nombre_empty"


# ═══════════════════════════════════════════════════════════════════
# Tests de Actualizar (con detección de ciclos)
# ═══════════════════════════════════════════════════════════════════
def test_actualizar_sin_cambiar_parent() -> None:
    repo = FakeCategoriaRepository()
    ciencias = repo.create(nombre="Ciencias", parent_id=None, descripcion=None)
    fisica = repo.create(nombre="Física", parent_id=ciencias.id, descripcion=None)

    out = ActualizarCategoriaUseCase(repo).execute(
        fisica.id,
        CategoriaInputDTO(nombre="Física Moderna", descripcion="Actualizada"),
        change_parent=False,  # no cambiamos padre
    )
    assert out.nombre == "Física Moderna"
    assert out.parent_id == ciencias.id  # sigue igual


def test_actualizar_con_ciclo_falla() -> None:
    repo = FakeCategoriaRepository()
    ciencias = repo.create(nombre="Ciencias", parent_id=None, descripcion=None)
    fisica = repo.create(nombre="Física", parent_id=ciencias.id, descripcion=None)
    mecanica = repo.create(nombre="Mecánica", parent_id=fisica.id, descripcion=None)

    # Intentamos hacer Ciencias dependiente de Mecánica → ciclo.
    with pytest.raises(ValidationError) as exc_info:
        ActualizarCategoriaUseCase(repo).execute(
            ciencias.id,
            CategoriaInputDTO(nombre="Ciencias", parent_id=mecanica.id),
            change_parent=True,
        )
    assert exc_info.value.code == "categoria_ciclo"


def test_actualizar_convirtiendo_en_raiz() -> None:
    repo = FakeCategoriaRepository()
    ciencias = repo.create(nombre="Ciencias", parent_id=None, descripcion=None)
    fisica = repo.create(nombre="Física", parent_id=ciencias.id, descripcion=None)

    out = ActualizarCategoriaUseCase(repo).execute(
        fisica.id,
        CategoriaInputDTO(nombre="Física", parent_id=None),
        change_parent=True,
    )
    assert out.parent_id is None


# ═══════════════════════════════════════════════════════════════════
# Tests de Eliminar (con PROTECT)
# ═══════════════════════════════════════════════════════════════════
def test_eliminar_con_hijos_falla() -> None:
    repo = FakeCategoriaRepository()
    ciencias = repo.create(nombre="Ciencias", parent_id=None, descripcion=None)
    repo._protect_on_delete.add(ciencias.id)  # simula que tiene hijos

    with pytest.raises(ConflictError) as exc_info:
        EliminarCategoriaUseCase(repo).execute(ciencias.id)
    assert exc_info.value.code == "categoria_con_hijos"


def test_eliminar_inexistente_falla() -> None:
    repo = FakeCategoriaRepository()
    with pytest.raises(NotFoundError):
        EliminarCategoriaUseCase(repo).execute(uuid4())


# ═══════════════════════════════════════════════════════════════════
# Tests de Obtener y Subcategorías
# ═══════════════════════════════════════════════════════════════════
def test_obtener_inexistente_falla() -> None:
    with pytest.raises(NotFoundError):
        ObtenerCategoriaUseCase(FakeCategoriaRepository()).execute(uuid4())


def test_listar_subcategorias_padre_inexistente_falla() -> None:
    with pytest.raises(NotFoundError) as exc_info:
        ListarSubcategoriasUseCase(FakeCategoriaRepository()).execute(uuid4())
    assert exc_info.value.code == "categoria_not_found"


def test_listar_subcategorias_devuelve_hijos_directos() -> None:
    repo = FakeCategoriaRepository()
    ciencias = repo.create(nombre="Ciencias", parent_id=None, descripcion=None)
    fisica = repo.create(nombre="Física", parent_id=ciencias.id, descripcion=None)
    mecanica = repo.create(nombre="Mecánica", parent_id=fisica.id, descripcion=None)

    out = ListarSubcategoriasUseCase(repo).execute(ciencias.id)
    assert len(out) == 1
    assert out[0].nombre == "Física"
    # Mecánica (nieta) NO aparece, porque solo son hijos directos.
    assert mecanica.id not in [o.id for o in out]
