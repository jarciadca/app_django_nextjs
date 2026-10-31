"""DTOs del slice `articulos`."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class ArticuloInputDTO:
    """Datos de entrada para crear/actualizar un artículo."""

    titulo: str
    anio: int
    revista_id: UUID
    resumen: str = ""
    palabras_clave: str = ""
    doi: str | None = None
    idioma: str = "es"
    estado: str = "borrador"
    fecha_publicacion: date | None = None


@dataclass(frozen=True)
class ArticuloOutputDTO:
    """Datos de salida de un artículo."""

    id: UUID
    titulo: str
    resumen: str
    palabras_clave: str
    doi: str | None
    anio: int
    idioma: str
    estado: str
    fecha_publicacion: date | None
    revista_id: UUID
