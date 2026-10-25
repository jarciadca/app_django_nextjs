"""
Interfaces (puertos) del dominio `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
El `CategoriaRepository` define QUÉ operaciones necesita el dominio.
Cada método se corresponde con un endpoint o con una validación
invocada por un use case:

    Método del repo           →   Endpoint REST / Acción interna
    ─────────────────────────────────────────────────────────────
    list()                    →   GET    /api/categorias/
                                  (con ?search=, ?ordering=,
                                   ?only_roots=, ?parent=,
                                   ?page=, ?page_size=)
    get_by_id()               →   GET    /api/categorias/<uuid>/
    list_children()           →   GET    /api/categorias/<uuid>/subcategorias/
    create()                  →   POST   /api/categorias/
    update()                  →   PUT    /api/categorias/<uuid>/
    delete()                  →   DELETE /api/categorias/<uuid>/
    get_ancestor_ids()        →   (helper del use case para detectar ciclos)

La firma es un `Protocol`: cualquier implementación (Django ORM,
en memoria, fake) que ofrezca estos métodos cumple el contrato.
════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

# `Protocol` para tipado estructural.
from typing import Protocol

# `UUID` para tipar ids.
from uuid import UUID

# Entidad del dominio.
from features.categorias.domain.entities import Categoria


class CategoriaRepository(Protocol):
    """Interfaz del repositorio de categorías."""

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
        """
        Lista categorías con filtros.

        Args:
            search: `?search=nombre_o_descripcion`.
            ordering: `?ordering=nombre` o `?ordering=-created_at`.
            parent_id: `?parent=<uuid>` → hijos directos de esa categoría.
            only_roots: `?only_roots=true` → solo categorías raíz (sin padre).
                        API: útil para construir el primer nivel del árbol.
            offset, limit: paginación (`(page-1)*page_size`, `page_size`).

        Returns:
            (lista de categorías, total sin paginar)

        Nota API:
            - Si `parent_id` y `only_roots` vienen a la vez, `parent_id`
              tiene prioridad (el filtro más específico).
            - La respuesta JSON es PLANA (cada categoría con su parent_id),
              no anidada.
        """
        ...

    def get_by_id(self, categoria_id: UUID) -> Categoria | None:
        """Busca una categoría por UUID. API: GET /api/categorias/<uuid>/."""
        ...

    def list_children(self, parent_id: UUID) -> list[Categoria]:
        """
        Devuelve los hijos directos de una categoría.

        API: endpoint extra GET /api/categorias/<uuid>/subcategorias/.
        No pagina (los hijos directos suelen ser pocos). Si un usuario
        tiene cientos de hijos, sería señal de diseño a revisar.
        """
        ...

    def create(
        self,
        *,
        nombre: str,
        parent_id: UUID | None,
        descripcion: str | None,
    ) -> Categoria:
        """
        Crea una categoría.

        API: POST /api/categorias/. El use case valida:
          - nombre válido (VO).
          - si `parent_id` no es None, que exista esa categoría padre.
        """
        ...

    def update(
        self,
        categoria_id: UUID,
        *,
        nombre: str | None = None,
        parent_id: UUID | None = None,
        change_parent: bool = False,
        descripcion: str | None = None,
    ) -> Categoria | None:
        """
        Actualiza una categoría.

        `change_parent=True` indica que se quiere cambiar `parent_id`
        explícitamente (incluso a None para convertirla en raíz).
        Sin este flag, `parent_id=None` significa "no cambiar el padre".

        API: PUT /api/categorias/<uuid>/. El use case valida:
          - nombre válido (VO).
          - si cambia parent_id, que no se cree un ciclo.
          - si cambia parent_id a uno existente, que ese padre exista.
        """
        ...

    def delete(self, categoria_id: UUID) -> bool:
        """
        Elimina una categoría.

        API: DELETE /api/categorias/<uuid>/. Puede fallar con
        ProtectedError si la categoría tiene hijos → el use case lo
        capturará y lanzará ConflictError → 409 problem+json.

        Returns:
            True si existía y se borró.
        """
        ...

    def get_ancestor_ids(self, categoria_id: UUID) -> list[UUID]:
        """
        Devuelve los IDs de todos los ancestros hasta la raíz.

        Ejemplo: A (raíz) → B → C → D.
        get_ancestor_ids(D.id) → [C.id, B.id, A.id]

        API: NO es un endpoint. Es un HELPER invocado por el use case
        `ActualizarCategoriaUseCase` para detectar ciclos:
        si el nuevo `parent_id` está entre los ancestros de la categoría
        que estamos editando, se produce un ciclo → ValidationError → 400.
        """
        ...
