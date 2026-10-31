"""
Interfaces del dominio `articulos`.

IMPORTANTE: el método se llama `list_all` (no `list`) para evitar la
colisión con el built-in `list` que confunde a mypy en los Protocol.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol
from uuid import UUID

from features.articulos.domain.entities import Articulo


class ArticuloRepository(Protocol):
    """Interfaz del repositorio de artículos."""

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
        """Lista artículos con filtros y paginación."""
        ...

    def get_by_id(self, articulo_id: UUID) -> Articulo | None:
        """Busca por UUID."""
        ...

    def exists_by_doi(self, doi: str, exclude_id: UUID | None = None) -> bool:
        """True si ya existe un artículo con ese DOI (excluyendo un id)."""
        ...

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
        """Crea un artículo."""
        ...

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
        """Actualiza un artículo (solo campos no-None)."""
        ...

    def delete(self, articulo_id: UUID) -> bool:
        """Elimina un artículo."""
        ...
