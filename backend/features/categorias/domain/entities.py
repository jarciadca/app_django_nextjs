"""
Entidades del dominio `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
La entidad `Categoria` representa un nodo del árbol de categorías.
Se expone en la API como:

    {
      "id": "uuid-de-fisica",
      "nombre": "Física",
      "parent_id": "uuid-de-ciencias",   ← id del padre (o null si raíz)
      "descripcion": "..."
    }

El frontend reconstruye el árbol combinando `id` + `parent_id`.
Por eso NO devolvemos subcategorías anidadas: el JSON es plano.
Si el frontend quiere los hijos de una categoría concreta, llama a
GET /api/categorias/<uuid>/subcategorias/.

DECISIÓN: profundidad libre. Una categoría puede tener cualquier
número de ancestros. El frontend decide cuántos niveles renderizar.
════════════════════════════════════════════════════════════════════
"""

# `dataclass` para el boilerplate automático.
from dataclasses import dataclass

# `UUID` para tipar ids.
from uuid import UUID


@dataclass(frozen=True)
class Categoria:
    """
    Entidad que representa una categoría del árbol.

    Attributes:
        id: UUID del recurso.
        nombre: nombre visible (ej. "Física").
        parent_id: UUID del padre, o None si es raíz.
        descripcion: texto libre opcional.

    Relación con la API:
        - `id` → JSON "id", usado en URLs /api/categorias/<uuid>/.
        - `parent_id` → JSON "parent_id", permite reconstruir el árbol.
        - `nombre` → JSON "nombre".
        - `descripcion` → JSON "descripcion" (o null).
    """

    id: UUID
    nombre: str
    parent_id: UUID | None
    descripcion: str | None

    @property
    def is_root(self) -> bool:
        """
        True si la categoría es raíz (sin padre).

        API: expuesto como campo calculado si se necesita en algún filtro
        futuro (ej. `?is_root=true`). Por ahora no se expone en JSON,
        pero está disponible para la lógica interna.
        """
        return self.parent_id is None
