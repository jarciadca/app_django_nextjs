"""
Serializers DRF del slice `revistas`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Un Serializer de DRF cumple DOS funciones en la API:

  1) INPUT  (RevistaInputSerializer):
     Valida la FORMA del JSON entrante antes de que llegue al use case.
     Ejemplos de validaciones de forma:
        - ¿el campo "nombre" existe y es un string?
        - ¿"issn" tiene como máximo 9 caracteres?
        - ¿"sitio_web" es una URL con formato válido?
     Lo que NO hace:
        - NO valida el checksum del ISSN (eso es dominio, lo hace el use case).
        - NO comprueba si el ISSN ya existe (eso requiere BD, lo hace el repo).

  2) OUTPUT (RevistaOutputSerializer):
     Convierte el DTO de salida a JSON para la respuesta HTTP.
     Esta es la forma EXACTA que verá el frontend:
        {"id": "uuid", "nombre": "...", "issn": "...", ...}

Flujo:
    JSON request  → RevistaInputSerializer  → DTO → use case
    DTO response  ← RevistaOutputSerializer ← use case
════════════════════════════════════════════════════════════════════
"""

# `serializers` de DRF: contiene Serializer, CharField, URLField, etc.
from rest_framework import serializers


class RevistaInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    Valida el body de POST /api/revistas/ y PUT /api/revistas/<uuid>/.

    API: se instancia en `RevistasListView.post()` y en
    `RevistaDetailView.put()`. Si falla la validación, DRF lanza
    ValidationError de DRF → el handler global la traduce a 400
    problem+json (con el detalle por campo).

    Forma esperada del JSON:
        {
          "nombre": "Nature",              ← obligatorio
          "issn": "0028-0836",             ← obligatorio
          "editorial": "Springer",         ← opcional
          "pais": "GB",                    ← opcional
          "sitio_web": "https://..."       ← opcional
        }

    Nota: `# type: ignore[type-arg]` es porque mypy estricto exige
    parámetro genérico a `Serializer`, pero DRF no lo tipa aún.
    Es una concesión pragmática documentada.
    """

    # ─── Campo: nombre ───
    # API: string JSON, requerido, max 255 caracteres.
    # Si falta o excede longitud → 400 problem+json.
    nombre = serializers.CharField(max_length=255)

    # ─── Campo: issn ───
    # API: string JSON, requerido, max 9 caracteres.
    # La validación de FORMATO (regex XXXX-XXXX) y CHECKSUM la hace
    # el use case con el VO `ISSN`. Aquí solo validamos que sea string
    # y no exceda 9 chars, para dar un 400 rápido si el cliente envía
    # basura evidente (ej. un número o 30 caracteres).
    issn = serializers.CharField(max_length=9)

    # ─── Campo: editorial ───
    # API: opcional. Puede no venir (`required=False`).
    # `allow_null=True`: acepta `null` explícito.
    # `allow_blank=True`: acepta `""` (string vacío).
    editorial = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    # ─── Campo: pais ───
    # API: opcional, código ISO de 2 letras.
    # `max_length=2`: validación de forma (evita "Reino Unido").
    # La normalización a mayúsculas la hace el use case (`.upper()`).
    pais = serializers.CharField(
        max_length=2,
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    # ─── Campo: sitio_web ───
    # API: opcional, pero si viene debe ser URL válida.
    # `URLField`: valida formato (http://, https://).
    # Si es inválido → 400 problem+json con el detalle del campo.
    sitio_web = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class RevistaOutputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    Serializa un `RevistaOutputDTO` a JSON público.

    API: se instancia con `RevistaOutputSerializer(dto).data` para
    UN DTO, o `RevistaOutputSerializer(lista, many=True).data` para
    una lista. Define la forma EXACTA que verá el frontend.

    Ejemplo de JSON producido:
        {
          "id": "f5134d90-32af-4058-a21b-30a1cbdbba8f",
          "nombre": "Nature",
          "issn": "0028-0836",
          "editorial": "Springer",
          "pais": "GB",
          "sitio_web": "https://www.nature.com"
        }
    """

    # UUID serializado como string en el JSON.
    # API: el frontend usa este valor para /api/revistas/<uuid>/.
    id = serializers.UUIDField()

    # Resto de campos: mismos tipos que en el DTO.
    nombre = serializers.CharField()
    issn = serializers.CharField()

    # `allow_null=True` en los opcionales para que el JSON pueda
    # devolver `null` cuando el campo está vacío en BD.
    editorial = serializers.CharField(allow_null=True)
    pais = serializers.CharField(allow_null=True)
    sitio_web = serializers.CharField(allow_null=True)
