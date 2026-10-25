"""
Interfaces (puertos) del dominio `revistas`.

En hexagonal, el dominio declara QUÉ necesita del exterior (persistencia)
sin saber CÓMO se implementa. La implementación concreta (Django ORM) vive
en infrastructure/repositories.py.

Esto permite:
  - Testear casos de uso con repositorios fake (sin BD).
  - Cambiar ORM sin tocar dominio ni aplicación.
"""

# `Protocol` permite tipado estructural: cualquier clase que implemente
# estos métodos cumple el contrato, sin heredar de nada.
from typing import Protocol

# `UUID` para tipar ids.
from uuid import UUID

# Importamos la entidad (misma capa).
from features.revistas.domain.entities import Revista


class RevistaRepository(Protocol):
    """
    Interfaz del repositorio de revistas.

    Contrato: cualquier implementación (Django ORM, en memoria, fake)
    debe ofrecer estos 6 métodos con estas firmas exactas.
    """

    def list_all(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Revista], int]:
        """
        Lista revistas con filtros y paginación.

        Args:
            search: término de búsqueda libre (nombre/issn/editorial).
            ordering: campo y dirección, ej. "-nombre".
            offset: cuántos registros saltar (para paginación).
            limit: cuántos devolver (page_size).

        Returns:
            (lista de revistas de esta página, total sin paginar)
        """
        ...

    def get_by_id(self, revista_id: UUID) -> Revista | None:
        """
        Busca una revista por id.

        Returns:
            La revista, o None si no existe.
        """
        ...

    def exists_by_issn(self, issn: str, exclude_id: UUID | None = None) -> bool:
        """
        Comprueba si ya existe una revista con ese ISSN.

        Args:
            issn: ISSN ya validado (string normalizado).
            exclude_id: si se indica, excluye ese id (útil al actualizar).

        Returns:
            True si ya existe, False si no.
        """
        ...

    def create(
        self,
        *,
        nombre: str,
        issn: str,
        editorial: str | None,
        pais: str | None,
        sitio_web: str | None,
    ) -> Revista:
        """Crea una revista y devuelve la entidad resultante."""
        ...

    def update(
        self,
        revista_id: UUID,
        *,
        nombre: str | None = None,
        issn: str | None = None,
        editorial: str | None = None,
        pais: str | None = None,
        sitio_web: str | None = None,
    ) -> Revista | None:
        """
        Actualiza una revista. Los campos `None` no se tocan.

        Returns:
            La entidad actualizada, o None si no existía.
        """
        ...

    def delete(self, revista_id: UUID) -> bool:
        """
        Elimina una revista.

        Returns:
            True si existía y se borró, False si no existía.
        """
        ...
