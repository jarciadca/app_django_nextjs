"""
DTOs del slice `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Los DTOs aíslan al use case del formato HTTP. La vista construye
`CategoriaInputDTO` desde el JSON validado por el serializer, y
recibe `CategoriaOutputDTO` para serializar la respuesta.

Forma del JSON de salida (plana, con parent_id):
    {
      "id": "uuid",
      "nombre": "Física",
      "parent_id": "uuid-del-padre",   ← o null si raíz
      "descripcion": "..."             ← o null
    }
════════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CategoriaInputDTO:
    """
    Datos de entrada para crear/actualizar una categoría.

    API: la vista lo construye desde `request.data` validado por
    `CategoriaInputSerializer`. Los campos opcionales (`None`)
    significan "no proporcionado" para el use case.

    Nota sobre `parent_id`: si es None en el input de un POST, la
    categoría se crea como raíz. En un PUT, la semántica depende de
    si el campo viene explícito o no (ver `ActualizarCategoriaUseCase`).
    """

    nombre: str
    parent_id: UUID | None = None
    descripcion: str | None = None


@dataclass(frozen=True)
class CategoriaOutputDTO:
    """
    Datos de salida de una categoría.

    API: el serializer lo convierte al JSON plano que verá el frontend.
    """

    id: UUID
    nombre: str
    parent_id: UUID | None
    descripcion: str | None
