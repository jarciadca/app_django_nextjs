"""
Value Objects del dominio `revistas`.

Contiene las reglas de negocio puras sobre los datos de una revista.
La más importante: validación de ISSN con checksum.
"""

# `re` para el regex de formato ISSN.
import re

# Excepción de dominio: el handler global la traducirá a HTTP 400.
from shared.domain.exceptions import ValidationError


class ISSN:
    """
    Value Object para el identificador ISSN.

    Formato: XXXX-XXXX (8 dígitos, el último puede ser X).
    Incluye validación del dígito verificador (checksum módulo 11).

    Regla del checksum:
        - Se toman los 7 primeros dígitos.
        - Cada uno se multiplica por un peso decreciente: 8,7,6,5,4,3,2.
        - Se suman los productos.
        - Se calcula: 11 - (suma % 11).
        - Si da 11 → verificador = 0.
        - Si da 10 → verificador = 'X'.
        - En otro caso → verificador = el número.
        - El 8º carácter del ISSN debe coincidir con ese verificador.
    """

    # Regex estricta: 4 dígitos, guion, 3 dígitos y un dígito o X al final.
    ISSN_RE = re.compile(r"^\d{4}-\d{3}[\dX]$")

    def __init__(self, value: str) -> None:
        # Normalizamos: quitamos espacios y pasamos a mayúsculas (para 'X').
        value = value.strip().upper()

        # 1) Validamos el formato.
        if not self.ISSN_RE.match(value):
            raise ValidationError(
                "El ISSN debe tener formato XXXX-XXXX (último puede ser X).",
                code="issn_invalid_format",
            )

        # 2) Extraemos los 8 dígitos sin guion.
        digits = value.replace("-", "")

        # 3) Calculamos el dígito verificador esperado.
        total = 0
        for i, ch in enumerate(digits[:7]):
            total += int(ch) * (8 - i)

        remainder = total % 11
        expected = 11 - remainder

        # 4) Si el verificador calculado es 11, en realidad es 0.
        if expected == 11:
            expected_char = "0"
        # 5) Si es 10, en realidad es 'X'.
        elif expected == 10:
            expected_char = "X"
        else:
            expected_char = str(expected)

        # 6) Comparamos con el 8º carácter.
        if digits[7] != expected_char:
            raise ValidationError(
                "El dígito verificador del ISSN no es válido.",
                code="issn_invalid_checksum",
            )

        # Si todo pasa, guardamos el valor normalizado.
        self._value = value

    @property
    def value(self) -> str:
        """Devuelve el ISSN normalizado (mayúsculas, con guion)."""
        return self._value
