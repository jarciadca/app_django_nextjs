"""
Value Objects del dominio `articulos`.

Cada VO valida reglas de negocio puras (formato, rangos) sobre un campo.
"""

import re

from shared.domain.exceptions import ValidationError


class Titulo:
    """Título del artículo: 1-500 chars, no vacío."""

    MIN_LENGTH = 1
    MAX_LENGTH = 500

    def __init__(self, value: str) -> None:
        value = value.strip()
        if len(value) < self.MIN_LENGTH:
            raise ValidationError("El título no puede estar vacío.", code="titulo_empty")
        if len(value) > self.MAX_LENGTH:
            raise ValidationError(
                f"El título no puede superar {self.MAX_LENGTH} caracteres.",
                code="titulo_too_long",
            )
        self._value = value

    @property
    def value(self) -> str:
        return self._value


class Anio:
    """Año de publicación: entero entre 1900 y 2100."""

    MIN = 1900
    MAX = 2100

    def __init__(self, value: int) -> None:
        if not (self.MIN <= value <= self.MAX):
            raise ValidationError(
                f"El año debe estar entre {self.MIN} y {self.MAX}.",
                code="anio_invalid",
            )
        self._value = value

    @property
    def value(self) -> int:
        return self._value


class Idioma:
    """Código ISO 639-1 de 2 letras minúsculas (es, en, fr...)."""

    IDIOMA_RE = re.compile(r"^[a-z]{2}$")

    def __init__(self, value: str) -> None:
        value = value.strip().lower()
        if not self.IDIOMA_RE.match(value):
            raise ValidationError(
                "El idioma debe ser un código ISO 639-1 (2 letras minúsculas).",
                code="idioma_invalid",
            )
        self._value = value

    @property
    def value(self) -> str:
        return self._value


class DOI:
    """
    Digital Object Identifier.

    Formato básico: 10.XXXX/sufijo. Ej: 10.1038/nature12345.
    Si el valor es None o vacío, se considera "sin DOI".
    """

    DOI_RE = re.compile(r"^10\.\d{4,9}/.+$")

    def __init__(self, value: str | None) -> None:
        if value is None or not value.strip():
            self._value: str | None = None
            return
        value = value.strip()
        if not self.DOI_RE.match(value):
            raise ValidationError(
                "El DOI no tiene un formato válido (debe empezar por 10.XXXX/...).",
                code="doi_invalid",
            )
        self._value = value

    @property
    def value(self) -> str | None:
        return self._value


class EstadoArticulo:
    """Estado del artículo: solo 'borrador' o 'publicado'."""

    VALIDOS = {"borrador", "publicado"}

    def __init__(self, value: str) -> None:
        value = value.strip().lower()
        if value not in self.VALIDOS:
            raise ValidationError(
                "El estado debe ser 'borrador' o 'publicado'.",
                code="estado_invalid",
            )
        self._value = value

    @property
    def value(self) -> str:
        return self._value
