"""
Entidades del dominio `autores`.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Autor:
    """
    Entidad de dominio que representa un autor académico.

    Attributes:
        id: UUID del autor.
        nombre: nombre de pila.
        apellido: apellido(s).
        email: email de contacto (puede repetirse entre autores).
        afiliacion: institución a la que pertenece.
        orcid: identificador ORCID (formato 0000-0000-0000-000X). Opcional.
        pais: código ISO de país (ej. "ES", "MX"). Opcional.
        bio: biografía breve. Opcional.
        foto: ruta relativa de la foto en MEDIA_ROOT. Opcional.
    """

    id: UUID
    nombre: str
    apellido: str
    email: str
    afiliacion: str
    orcid: str | None
    pais: str | None
    bio: str | None
    foto: str | None

    @property
    def nombre_completo(self) -> str:
        """Nombre completo: 'Nombre Apellido'."""
        return f"{self.nombre} {self.apellido}".strip()
