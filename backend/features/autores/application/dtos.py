"""
DTOs del slice `autores`.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AutorInputDTO:
    """Datos de entrada para crear/actualizar autor."""

    nombre: str
    apellido: str
    email: str
    afiliacion: str = ""
    orcid: str | None = None
    pais: str | None = None
    bio: str | None = None


@dataclass(frozen=True)
class AutorOutputDTO:
    """Datos de salida de un autor."""

    id: UUID
    nombre: str
    apellido: str
    email: str
    afiliacion: str
    orcid: str | None
    pais: str | None
    bio: str | None
    foto: str | None
