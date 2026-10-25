"""
Implementación Django ORM del repositorio de categorías.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Esta clase implementa `CategoriaRepository` (Protocol del dominio).
Cada método se corresponde con un endpoint o helper:

    Método del repo           →   Endpoint REST / Acción interna
    ─────────────────────────────────────────────────────────────
    list_all()                →   GET    /api/categorias/
                                  (con ?search=, ?ordering=,
                                   ?parent=, ?only_roots=,
                                   ?page=, ?page_size=)
    get_by_id()               →   GET    /api/categorias/<uuid>/
    list_children()           →   GET    /api/categorias/<uuid>/subcategorias/
    create()                  →   POST   /api/categorias/
    update()                  →   PUT    /api/categorias/<uuid>/
    delete()                  →   DELETE /api/categorias/<uuid>/
    get_ancestor_ids()        →   (helper del use case para ciclos)

IMPORTANTE:
    El método se llama `list_all` (no `list`) porque si se llamara `list`,
    mypy fallaría en el Protocol del dominio (`list` colisiona con el
    built-in `list`). Ya lo corregimos en 4b.7.
════════════════════════════════════════════════════════════════════
"""

# Necesitamos `from __future__ import annotations` también aquí, por
# la misma razón que en el Protocol: para tipar `list[Categoria]` sin
# que mypy se confunda con nombres. En este archivo no hay colisión
# porque el método se llama `list_all`, pero lo añadimos por
# consistencia con el resto de repositorios del proyecto.
from __future__ import annotations

# `UUID` para tipar ids.
from uuid import UUID

# `Q` de Django para construir queries OR.
# API: usado en `?search=` para buscar en nombre OR descripción.
from django.db.models import Q

# Entidad del dominio.
from features.categorias.domain.entities import Categoria

# Modelo Django. Alias `as CategoriaModel` para no colisionar con la
# entidad `Categoria` del dominio.
from features.categorias.infrastructure.models import Categoria as CategoriaModel


def _to_entity(model: CategoriaModel) -> Categoria:
    """
    Convierte un modelo Django `Categoria` en la entidad de dominio.

    API: esta función se invoca ANTES de devolver datos al use case.
    El use case nunca ve modelos Django, solo entidades.

    Args:
        model: instancia del modelo Django.

    Returns:
        Entidad inmutable `Categoria` del dominio.
    """
    return Categoria(
        id=model.id,
        nombre=model.nombre,
        parent_id=model.parent_id,
        descripcion=model.descripcion,
    )


class DjangoCategoriaRepository:
    """
    Implementación Django ORM de `CategoriaRepository`.

    API: se instancia nueva por request (es barata). La vista crea
    `DjangoCategoriaRepository()` y la pasa al use case.
    """

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: list_all
    # API: GET /api/categorias/
    #      Acepta ?search=, ?ordering=, ?parent=, ?only_roots=, ?page=
    # ═══════════════════════════════════════════════════════════════
    def list_all(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        parent_id: UUID | None = None,
        only_roots: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Categoria], int]:
        """
        Lista categorías con filtros y paginación.

        Args:
            search: `?search=texto`. Busca en nombre OR descripción.
            ordering: `?ordering=nombre` o `?ordering=-created_at`.
                      Lista blanca para seguridad.
            parent_id: `?parent=<uuid>`. Filtra hijos directos de esa
                       categoría. Si se indica, tiene prioridad sobre
                       `only_roots`.
            only_roots: `?only_roots=true`. Solo categorías raíz
                        (parent_id IS NULL).
            offset, limit: paginación.

        Returns:
            (lista de categorías de esta página, total sin paginar)

        Nota API: el JSON resultante es PLANO. Cada categoría lleva su
        `parent_id`. El frontend reconstruye el árbol combinando `id`
        y `parent_id`.
        """
        # Queryset base: todas las categorías.
        qs = CategoriaModel.objects.all()

        # ─── Filtro por padre (más específico, tiene prioridad) ───
        # API: `?parent=<uuid>` → hijos directos.
        if parent_id is not None:
            qs = qs.filter(parent_id=parent_id)
        # ─── Filtro por raíz ───
        # API: `?only_roots=true` → solo categorías sin padre.
        # Nota: `parent_id is None` ya cubre este caso, así que los
        # dos filtros son mutuamente excluyentes por diseño (si vienen
        # ambos, `parent_id` gana porque se aplicó primero).
        elif only_roots:
            qs = qs.filter(parent__isnull=True)

        # ─── Búsqueda libre ───
        # API: `?search=texto` → nombre OR descripción.
        # `Q(a) | Q(b)` se traduce a `WHERE a ILIKE ... OR b ILIKE ...`.
        if search:
            q = search.strip()
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))

        # ─── Ordenamiento con lista blanca ───
        # API: `?ordering=nombre` o `?ordering=-created_at`.
        # SEGURIDAD: solo permitimos estos campos para evitar inyección.
        allowed_ordering = {"nombre", "created_at"}
        if ordering and ordering.lstrip("-") in allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            # Default: el orden definido en Meta.ordering = ["nombre"].
            qs = qs.order_by("nombre")

        # ─── Total y paginación ───
        total = qs.count()
        page = qs[offset : offset + limit]

        # ─── Conversión a entidades ───
        return [_to_entity(m) for m in page], total

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: get_by_id
    # API: GET /api/categorias/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def get_by_id(self, categoria_id: UUID) -> Categoria | None:
        """
        Busca una categoría por UUID.

        API: usado por GET /api/categorias/<uuid>/.
        Si devuelve None, el use case lanza NotFoundError → 404.

        Args:
            categoria_id: UUID del recurso.

        Returns:
            La entidad, o None si no existe.
        """
        try:
            model = CategoriaModel.objects.get(id=categoria_id)
        except CategoriaModel.DoesNotExist:
            return None
        return _to_entity(model)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: list_children
    # API: GET /api/categorias/<uuid>/subcategorias/
    # ═══════════════════════════════════════════════════════════════
    def list_children(self, parent_id: UUID) -> list[Categoria]:
        """
        Devuelve los hijos directos (subcategorías de primer nivel) de
        una categoría.

        API: alimenta el endpoint extra
             GET /api/categorias/<uuid>/subcategorias/.
             No pagina: los hijos directos suelen ser pocos (si un
             usuario tiene cientos, es señal de diseño a revisar).

        SQL: SELECT * FROM categorias_categoria
             WHERE parent_id = <uuid>
             ORDER BY nombre  (por Meta.ordering)

        Args:
            parent_id: UUID de la categoría padre.

        Returns:
            Lista de entidades hijas directas, ordenadas por nombre.
        """
        children = CategoriaModel.objects.filter(parent_id=parent_id)
        return [_to_entity(m) for m in children]

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: create
    # API: POST /api/categorias/
    # ═══════════════════════════════════════════════════════════════
    def create(
        self,
        *,
        nombre: str,
        parent_id: UUID | None,
        descripcion: str | None,
    ) -> Categoria:
        """
        Crea una categoría nueva.

        API: POST /api/categorias/.
        El use case valida antes de llamar aquí:
          - nombre no vacío (VO NombreCategoria).
          - si parent_id != None, que exista esa categoría padre.

        Args:
            nombre: nombre ya validado por el VO.
            parent_id: UUID del padre, o None si es raíz.
            descripcion: texto opcional.

        Returns:
            La entidad creada con id UUID asignado.
        """
        model = CategoriaModel.objects.create(
            nombre=nombre,
            parent_id=parent_id,
            descripcion=descripcion,
        )
        return _to_entity(model)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: update
    # API: PUT /api/categorias/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def update(
        self,
        categoria_id: UUID,
        *,
        nombre: str | None = None,
        parent_id: UUID | None = None,
        change_parent: bool = False,
        descripcion: str | None = None,
    ) -> Categoria | None:
        """
        Actualiza una categoría existente.

        API: PUT /api/categorias/<uuid>/.
        El `change_parent=True` es crucial: sin él, `parent_id=None`
        se interpretaría como "no cambiar" (default). Con él, `parent_id=None`
        significa "convertir en raíz".

        Args:
            categoria_id: UUID a actualizar.
            nombre: nuevo nombre (None = no cambiar).
            parent_id: nuevo padre (None + change_parent=True = raíz).
            change_parent: si True, aplica el nuevo parent_id.
            descripcion: nueva descripción (None = no cambiar).

        Returns:
            Entidad actualizada, o None si no existía.

        Nota API: la validación de ciclos NO está aquí, está en el use
        case (que usa `get_ancestor_ids`). Aquí solo persistimos.
        """
        try:
            model = CategoriaModel.objects.get(id=categoria_id)
        except CategoriaModel.DoesNotExist:
            return None

        # Actualizamos solo los campos no-None explícitos.
        if nombre is not None:
            model.nombre = nombre
        if change_parent:
            # `change_parent=True` → aplica parent_id, incluso si es None.
            # Así se puede convertir una subcategoría en raíz.
            model.parent_id = parent_id
        if descripcion is not None:
            model.descripcion = descripcion

        model.save()
        return _to_entity(model)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: delete
    # API: DELETE /api/categorias/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def delete(self, categoria_id: UUID) -> bool:
        """
        Elimina una categoría.

        API: DELETE /api/categorias/<uuid>/.
        ⚠️ Puede lanzar `django.db.models.ProtectedError` si la categoría
        tiene hijos (por `on_delete=PROTECT`). El use case captura esa
        excepción y la traduce a ConflictError → 409 problem+json.

        Args:
            categoria_id: UUID a borrar.

        Returns:
            True si existía y se borró.

        Raises:
            ProtectedError: si tiene hijos.
        """
        # `filter().delete()` devuelve (num_borrados, detalles).
        # Pero OJO: si la categoría tiene hijos y PROTECT está activo,
        # Django lanza ProtectedError ANTES de borrar nada.
        deleted, _ = CategoriaModel.objects.filter(id=categoria_id).delete()
        return deleted > 0

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: get_ancestor_ids
    # API: NO es endpoint. Es un HELPER para el use case.
    #      Lo usa `ActualizarCategoriaUseCase` para detectar ciclos.
    # ═══════════════════════════════════════════════════════════════
    def get_ancestor_ids(self, categoria_id: UUID) -> list[UUID]:
        """
        Devuelve los UUIDs de todos los ancestros de una categoría,
        de más cercano a más lejano (padre, abuelo, ...).

        Ejemplo:
            Ciencias (raíz) → Física → Mecánica Cuántica
            get_ancestor_ids(mecanica.id) → [fisica.id, ciencias.id]

        API: no se expone. Es un helper interno para detectar ciclos
        al cambiar `parent_id`. El algoritmo del use case:

            ancestros = repo.get_ancestor_ids(nuevo_padre_id)
            if categoria_id in ancestros:
                raise ValidationError("ciclo detectado")

        Implementación: recorre hacia ARRIBA desde `categoria_id`,
        siguiendo `parent_id` en cada paso.

        Args:
            categoria_id: UUID de la categoría desde la que empezar a subir.

        Returns:
            Lista de UUIDs de ancestros (padre primero, luego abuelo...).
            Lista vacía si la categoría es raíz o no existe.
        """
        ancestors: list[UUID] = []
        # Empezamos desde el padre de la categoría (no ella misma).
        current_id = categoria_id
        guard = 0
        # Guard de seguridad: máximo 100 niveles. Si alguien metiera un
        # ciclo en BD (que no debería pasar por la validación del use case),
        # evitaríamos un bucle infinito.
        while guard < 100:
            row = (
                CategoriaModel.objects.filter(id=current_id)
                .values_list("parent_id", flat=True)
                .first()
            )
            if row is None:
                break  # No existe o es raíz
            ancestors.append(row)
            current_id = row
            guard += 1
        return ancestors
