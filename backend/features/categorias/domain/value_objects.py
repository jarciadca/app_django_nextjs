"""
Value Objects del dominio `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Los VOs validan reglas de negocio simples sobre los campos. Si un
VO falla, el use case lanza ValidationError → handler global → 400
problem+json con código específico.

En categorías solo hay un VO: `NombreCategoria`. La jerarquía (parent_id)
y la detección de ciclos NO son VOs: son reglas del use case.
════════════════════════════════════════════════════════════════════
"""

# Importamos la excepción de dominio compartida.
from shared.domain.exceptions import ValidationError


class NombreCategoria:
    """
    Value Object para el nombre de una categoría.

    Reglas:
        - 1 a 150 caracteres (tras `strip()`).
        - No puede ser solo espacios.
        - Los caracteres pueden ser cualquier cosa (no validamos regex
          porque las categorías pueden tener tildes, ñ, etc.).

    API: si falla → 400 problem+json con `title: "nombre_empty"` o
    `"nombre_too_long"` según el caso.
    """

    MIN_LENGTH = 1
    MAX_LENGTH = 150

    def __init__(self, value: str) -> None:
        # Quitamos espacios antes/después.
        value = value.strip()

        # Validación de no vacío.
        if len(value) < self.MIN_LENGTH:
            raise ValidationError(
                "El nombre no puede estar vacío.",
                code="nombre_empty",
            )

        # Validación de longitud máxima.
        if len(value) > self.MAX_LENGTH:
            raise ValidationError(
                f"El nombre no puede superar {self.MAX_LENGTH} caracteres.",
                code="nombre_too_long",
            )

        # Guardamos el valor normalizado.
        self._value = value

    @property
    def value(self) -> str:
        """Valor validado (sin espacios alrededor)."""
        return self._value
