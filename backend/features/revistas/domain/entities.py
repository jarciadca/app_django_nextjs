"""
Entidades del dominio `revistas`.

Entidad = objeto con identidad propia (UUID) que representa un concepto
del negocio. Inmutable (`frozen=True`), sin dependencias de Django.
"""

# `dataclass` genera __init__, __repr__, __eq__ automáticamente.
from dataclasses import dataclass

# `UUID` para tipar el id.
from uuid import UUID


@dataclass(frozen=True)
class Revista:
    """
    Entidad que representa una revista académica.

    Attributes:
        id: UUID del recurso.
        nombre: nombre visible de la revista.
        issn: identificador único (validado por el VO ISSN).
        editorial: editorial que la publica (opcional).
        pais: código ISO de país de 2 letras (opcional).
        sitio_web: URL del sitio web (opcional).
    """

    id: UUID
    nombre: str
    issn: str
    editorial: str | None
    pais: str | None
    sitio_web: str | None
