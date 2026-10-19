"""
Value Objects del dominio `autores`.
"""

import re

from shared.domain.exceptions import ValidationError


class NombreAutor:
    """
    Value Object para el nombre o apellido de un autor.

    Reglas:
        - 1-150 caracteres tras quitar espacios.
        - No puede ser solo espacios.
    """

    def __init__(self, value: str, campo: str = "nombre") -> None:
        value = value.strip()
        if not value:
            raise ValidationError(
                f"El {campo} no puede estar vacío.",
                code=f"{campo}_empty",
            )
        if len(value) > 150:
            raise ValidationError(
                f"El {campo} no puede superar 150 caracteres.",
                code=f"{campo}_too_long",
            )
        self._value = value

    @property
    def value(self) -> str:
        return self._value


class Orcid:
    """
    Value Object para el identificador ORCID.

    Formato: 0000-0000-0000-0000 (último dígito puede ser X).
    Regex oficial simplificada.
    """

    ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")

    def __init__(self, value: str | None) -> None:
        if value is None or not value.strip():
            self._value: str | None = None
            return
        value = value.strip()
        if not self.ORCID_RE.match(value):
            raise ValidationError(
                "El ORCID debe tener formato 0000-0000-0000-000X.",
                code="orcid_invalid_format",
            )
        self._value = value

    @property
    def value(self) -> str | None:
        return self._value


class Pais:
    """
    Value Object para el país.

    Acepta códigos ISO de 2 letras (ES, MX, AR).
    """

    PAIS_RE = re.compile(r"^[A-Z]{2}$")

    def __init__(self, value: str | None) -> None:
        if value is None or not value.strip():
            self._value: str | None = None
            return
        value = value.strip().upper()
        if not self.PAIS_RE.match(value):
            raise ValidationError(
                "El país debe ser un código ISO de 2 letras (ej. ES, MX).",
                code="pais_invalid_format",
            )
        self._value = value

    @property
    def value(self) -> str | None:
        return self._value
