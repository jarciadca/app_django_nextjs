"""
Value Objects del dominio `usuarios`.

Un Value Object es un objeto inmutable que representa un concepto del
dominio con sus propias reglas de validación. No tiene identidad propia
(dos `Username("pedro")` son iguales si el valor es el mismo).

Aquí validamos reglas de negocio ANTES de que el dato llegue al ORM.
"""

import re

from shared.domain.exceptions import ValidationError

# Reglas de username: 3-150 caracteres, letras, números y @/./+/-/_.
# Sigue la convención de Django, pero centralizada.
USERNAME_RE = re.compile(r"^[\w.@+-]+$")


class Username:
    """
    Value Object para el username.

    Reglas:
        - 3-150 caracteres.
        - Solo letras, números y @/./+/-/_.
        - No puede ser solo espacios.
    """

    def __init__(self, value: str) -> None:
        # Quitamos espacios al principio/final.
        value = value.strip()

        if not (3 <= len(value) <= 150):
            raise ValidationError(
                "El username debe tener entre 3 y 150 caracteres.",
                code="username_invalid_length",
            )

        if not USERNAME_RE.match(value):
            raise ValidationError(
                "El username solo puede contener letras, números y @/./+/-/_.",
                code="username_invalid_chars",
            )

        self._value = value

    @property
    def value(self) -> str:
        """Valor validado."""
        return self._value

    def __str__(self) -> str:
        return self._value


class Email:
    """
    Value Object para el email.

    Reglas:
        - Formato básico (contiene @ y dominio).
        - Se normaliza a minúsculas.
    """

    # Regex simple; la validación fuerte la hace Django en el modelo.
    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, value: str) -> None:
        value = value.strip().lower()

        if not self.EMAIL_RE.match(value):
            raise ValidationError(
                "El email no tiene un formato válido.",
                code="email_invalid_format",
            )

        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value


class Password:
    """
    Value Object para la contraseña (SIN hashear).

    Reglas:
        - Al menos 8 caracteres.
        - No puede ser solo espacios.

    OJO: este VO solo valida el formato. El hasheo lo hace Django
    (set_password) en la capa de infraestructura. NO guardamos nunca
    el password en claro.
    """

    MIN_LENGTH = 8

    def __init__(self, value: str) -> None:
        if not value or value.isspace():
            raise ValidationError(
                "La contraseña no puede estar vacía.",
                code="password_empty",
            )

        if len(value) < self.MIN_LENGTH:
            raise ValidationError(
                f"La contraseña debe tener al menos {self.MIN_LENGTH} caracteres.",
                code="password_too_short",
            )

        self._value = value

    @property
    def value(self) -> str:
        """Valor en claro. Usar solo para pasarlo a set_password."""
        return self._value
