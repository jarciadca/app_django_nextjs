"""
Entidades del dominio `articulos`.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class Articulo:
    """
    Entidad de dominio `Articulo`.

    En Fase 4c.1 solo lleva metadatos básicos + revista_id.
    En fases posteriores se le añadirán `autores` y `categorias`.
    """

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

    @property
    def esta_publicado(self) -> bool:
        """True si el estado es 'publicado'."""
        return self.estado == "publicado"
