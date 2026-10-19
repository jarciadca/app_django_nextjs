"""
Interfaces de repositorios del dominio `autores`.
"""

from typing import Protocol
from uuid import UUID

from features.autores.domain.entities import Autor


class AutorRepository(Protocol):
    """Interfaz del repositorio de autores."""

    def list(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Autor], int]:
        """
        Lista autores con paginación.

        Returns:
            (lista_de_autores, total_de_autores_sin_paginar)
        """
        ...

    def get_by_id(self, autor_id: UUID) -> Autor | None:
        """Busca un autor por UUID."""
        ...

    def create(
        self,
        *,
        nombre: str,
        apellido: str,
        email: str,
        afiliacion: str,
        orcid: str | None,
        pais: str | None,
        bio: str | None,
        foto: str | None,
    ) -> Autor:
        """Crea un autor y lo persiste."""
        ...

    def update(
        self,
        autor_id: UUID,
        *,
        nombre: str | None = None,
        apellido: str | None = None,
        email: str | None = None,
        afiliacion: str | None = None,
        orcid: str | None = None,
        pais: str | None = None,
        bio: str | None = None,
        foto: str | None = None,
    ) -> Autor | None:
        """
        Actualiza un autor (solo los campos no-None).
        Devuelve la entidad actualizada, o None si no existe.
        """
        ...

    def delete(self, autor_id: UUID) -> bool:
        """Elimina un autor. True si existía y se eliminó."""
        ...
