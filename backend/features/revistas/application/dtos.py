"""
DTOs del slice `revistas`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Un DTO (Data Transfer Object) es un objeto plano que transporta datos
entre capas. Aquí cumplen DOS funciones:

  1) Input DTO  (RevistaInputDTO):
     Lo construye la VISTA a partir del JSON ya validado por el serializer.
     Es lo que el USE CASE recibe. Aísla al use case del formato HTTP:
     si mañana la API cambia (GraphQL, gRPC, CLI), el use case no se toca.

  2) Output DTO (RevistaOutputDTO):
     Lo devuelve el USE CASE. Es lo que el SERIALIZER convierte a JSON.
     Aísla la forma de salida del modelo Django: si mañana cambia el
     esquema de la tabla, el DTO público no tiene por qué cambiar.

Flujo por endpoint:

    POST /api/revistas/
        JSON → Serializer → RevistaInputDTO → Use Case → RevistaOutputDTO → JSON

    GET /api/revistas/
        Query params → Use Case → [RevistaOutputDTO, ...] → JSON paginado

Los DTOs son `frozen=True` (inmutables) para evitar modificaciones
accidentales a media capa.
════════════════════════════════════════════════════════════════════
"""

# `dataclass` genera __init__, __repr__, __eq__ automáticamente.
from dataclasses import dataclass

# `UUID` para tipar el id del output (el input no lo lleva, lo asigna la BD).
from uuid import UUID


@dataclass(frozen=True)
class RevistaInputDTO:
    """
    Datos de entrada para crear o actualizar una revista.

    API: la vista lo construye desde `request.data` ya validado por
    `RevistaInputSerializer`. Los campos opcionales (`None`) significan
    "no proporcionado" y el use case decide cómo tratarlos.

    Ejemplo de JSON que genera este DTO:
        {
          "nombre": "Nature",
          "issn": "0028-0836",
          "editorial": "Springer Nature",
          "pais": "GB",
          "sitio_web": "https://www.nature.com"
        }
    """

    # Nombre visible de la revista. Obligatorio.
    # API: JSON `"nombre": "Nature"`. El serializer lo exige (`CharField`).
    nombre: str

    # ISSN con formato XXXX-XXXX (validado por VO ISSN en el use case).
    # API: JSON `"issn": "0028-0836"`. El serializer exige formato básico;
    # el use case valida checksum.
    issn: str

    # Editorial (opcional). None significa "no especificada".
    # API: JSON `"editorial": "..."` o `null`.
    editorial: str | None = None

    # País en código ISO 2 letras (opcional).
    # API: JSON `"pais": "GB"` o `null`.
    pais: str | None = None

    # URL del sitio web (opcional).
    # API: JSON `"sitio_web": "https://..."` o `null`.
    sitio_web: str | None = None


@dataclass(frozen=True)
class RevistaOutputDTO:
    """
    Datos de salida de una revista.

    API: el serializer `RevistaOutputSerializer` lo convierte a JSON.
    La forma EXACTA de este DTO define el contrato público de la API
    para /api/revistas/. Si añades un campo aquí y al serializer, el
    frontend lo recibe; si lo quitas, dejas de exponerlo.

    Ejemplo de JSON que se construye a partir de este DTO:
        {
          "id": "f5134d90-32af-4058-a21b-30a1cbdbba8f",
          "nombre": "Nature",
          "issn": "0028-0836",
          "editorial": "Springer Nature",
          "pais": "GB",
          "sitio_web": "https://www.nature.com"
        }
    """

    # UUID del recurso (PK). Coincide con el id del modelo.
    # API: el frontend lo usa para /api/revistas/<uuid>/.
    id: UUID

    # Resto de campos: mismos tipos que la entidad de dominio.
    nombre: str
    issn: str
    editorial: str | None
    pais: str | None
    sitio_web: str | None
