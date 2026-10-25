"""
Modelos Django del slice `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Este modelo representa la tabla `categorias_categoria` en PostgreSQL.
Cada fila es un nodo del árbol de categorías que el frontend verá
como un objeto JSON plano:

    {
      "id": "uuid-de-fisica",
      "nombre": "Física",
      "parent_id": "uuid-de-ciencias",   ← o null si es raíz
      "descripcion": "..."
    }

El frontend reconstruye el árbol combinando `id` + `parent_id`.

CARACTERÍSTICAS CLAVE RESPECTO A `revistas`:

1. `parent = ForeignKey("self")`:
   - Autorreferencia a la MISMA tabla.
   - Permite jerarquía ilimitada (profundidad libre, como decidiste).
   - Con `related_name="children"`, desde Python puedes hacer
     `categoria.children.all()` para obtener subcategorías directas.
   - `null=True, blank=True`: una categoría raíz tiene `parent=None`.

2. `on_delete=PROTECT`:
   - Si intentas borrar una categoría con hijos, Django NO borra
     en cascada. Lanza `ProtectedError`.
   - El use case (paso 4b.10) lo captura y lo traduce a ConflictError
     → 409 Conflict con mensaje claro.
   - Es la opción más segura: evita borrados accidentales masivos
     (imagina `DELETE /api/categorias/<uuid-ciencias>/` borrando
     toda la jerarquía de ciencias si fuera CASCADE).

3. `indexes = [Index(fields=["parent", "nombre"])]`:
   - Índice compuesto (parent, nombre) acelera dos consultas típicas:
     * `list_children(parent_id)`: SELECT * FROM categorias
       WHERE parent_id = X ORDER BY nombre.
     * Construir el primer nivel del árbol: SELECT * WHERE parent_id IS NULL
       ORDER BY nombre.
   - API: las consultas `GET /api/categorias/?only_roots=true` y
     `GET /api/categorias/<uuid>/subcategorias/` se benefician directamente.

4. `ordering = ["nombre"]`:
   - Orden por defecto en los querysets. Al buscar hijos directos,
     salen ordenados alfabéticamente, lo que es lo natural en un árbol.
════════════════════════════════════════════════════════════════════
"""

# `uuid` para generar identificadores únicos como PK.
import uuid

# `models` de Django: tipos de campo de BD.
from django.db import models


class Categoria(models.Model):
    """
    Categoría jerárquica de área de investigación.

    Representa el recurso REST `/api/categorias/`. Cada instancia es
    un nodo del árbol. El árbol se define con `parent`.

    Ejemplo de árbol:
        Ciencias (parent=None)
        ├── Física (parent=Ciencias)
        │   ├── Mecánica Cuántica (parent=Física)
        │   └── Relatividad (parent=Física)
        └── Biología (parent=Ciencias)
            └── Genética (parent=Biología)
    """

    # ──────────────────────────────────────────────────────────────
    # PK con UUID (mismo patrón que revistas y autores)
    # ──────────────────────────────────────────────────────────────
    # API: expuesto en JSON como "id". Usado en URLs
    #      /api/categorias/<uuid>/.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ──────────────────────────────────────────────────────────────
    # CAMPO: nombre
    # ──────────────────────────────────────────────────────────────
    # API: JSON "nombre": "Física".
    # `db_index=True`: se usa en filtros `?search=`.
    # `max_length=150`: coincide con el límite del VO `NombreCategoria`.
    nombre = models.CharField(max_length=150, db_index=True)

    # ──────────────────────────────────────────────────────────────
    # CAMPO: parent (autorreferencia)
    # ──────────────────────────────────────────────────────────────
    # API: expuesto como "parent_id" en el JSON.
    #
    # `"self"` → apunta a la MISMA tabla. Django lo interpreta como
    #           ForeignKey a este mismo modelo.
    #
    # `on_delete=PROTECT` → intentar borrar una categoría que tiene
    #                       hijos lanza ProtectedError. El use case lo
    #                       captura y devuelve 409 Conflict.
    #                       Alternativas descartadas:
    #                         - CASCADE: borraría toda la jerarquía (peligroso).
    #                         - SET_NULL: dejaría hijos huérfanos (confuso).
    #                         - SET_DEFAULT: no aplica aquí.
    #
    # `null=True, blank=True`:
    #   - null=True → permite NULL en BD cuando es raíz.
    #   - blank=True → permite "" en formularios Django (admin).
    #
    # `related_name="children"`:
    #   - Desde Python: `categoria.children.all()` → subcategorías directas.
    #   - En el admin de Django, muestra las subcategorías.
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )

    # ──────────────────────────────────────────────────────────────
    # CAMPO: descripcion
    # ──────────────────────────────────────────────────────────────
    # API: JSON "descripcion": "..." o null.
    # `TextField`: sin límite de longitud. Útil para descripciones largas.
    descripcion = models.TextField(blank=True, null=True)

    # ──────────────────────────────────────────────────────────────
    # METADATOS DE AUDITORÍA (no expuestos en la API por defecto)
    # ──────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Configuración del modelo.

        `ordering = ["nombre"]`:
            - Afecta a querysets sin `.order_by()` explícito.
            - API: si el repositorio no aplica `?ordering=`, este es
              el orden por defecto que verá el frontend.
            - En el árbol, ordenar alfabéticamente por nombre es natural.

        `indexes = [Index(fields=["parent", "nombre"])]`:
            - Índice compuesto que acelera:
                SELECT * WHERE parent_id = X ORDER BY nombre
            - API: usado por `list_children()` (endpoint /subcategorias/)
              y por `list_all(only_roots=True)`.
        """

        db_table = "categorias_categoria"
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["parent", "nombre"]),
        ]

    def __str__(self) -> str:
        """
        Representación legible: "Ciencias > Física > Mecánica Cuántica".

        API: no aparece en el JSON (el serializer construye eso), pero
        es útil en el admin y en logs de errores.

        Recorre hacia arriba los padres para mostrar la ruta completa.
        Tiene un guard (límite de 100 niveles) para evitar bucles
        infinitos si alguna vez hubiera un ciclo en BD (que no debería
        pasar por la validación del use case).
        """
        # Construimos la ruta de abajo hacia arriba.
        parts = [self.nombre]
        current = self.parent
        guard = 0
        while current is not None and guard < 100:
            parts.append(current.nombre)
            current = current.parent
            guard += 1
        # Invertimos para que quede "Ciencias > Física > Mecánica Cuántica".
        return " > ".join(reversed(parts))
