"""
Serializers DRF del slice `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Igual que en `revistas`: los serializers validan FORMA del JSON. La
lógica de negocio (existencia del padre, ciclos) va en el use case.

Forma del JSON de entrada:
    {
      "nombre": "Física",
      "parent_id": "uuid-o-null",  ← opcional
      "descripcion": "...",        ← opcional
    }

Forma del JSON de salida:
    {
      "id": "uuid",
      "nombre": "Física",
      "parent_id": "uuid-o-null",
      "descripcion": "..."
    }
════════════════════════════════════════════════════════════════════
"""

from rest_framework import serializers


class CategoriaInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    Valida el body de POST /api/categorias/ y PUT /api/categorias/<uuid>/.

    Campos:
      - nombre: obligatorio, 1-150 chars.
      - parent_id: opcional, UUID o null.
      - descripcion: opcional, cualquier texto.

    Nota sobre `parent_id`:
      - Si NO viene → en el use case, `parent_id` queda None → raíz.
      - Si viene con UUID → subcategoría.
      - Si viene explícito como null → en PUT con `change_parent=True`,
        convierte en raíz. En POST, se comporta igual que "no viene".
    """

    nombre = serializers.CharField(max_length=150)
    parent_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )
    descripcion = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
    )


class CategoriaOutputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """
    Serializa un `CategoriaOutputDTO` a JSON público.

    API: define la forma EXACTA que verá el frontend. El JSON es plano:
    cada categoría lleva su `parent_id`, y el frontend reconstruye el
    árbol combinando `id` + `parent_id`.
    """

    id = serializers.UUIDField()
    nombre = serializers.CharField()
    parent_id = serializers.UUIDField(allow_null=True)
    descripcion = serializers.CharField(allow_null=True)
