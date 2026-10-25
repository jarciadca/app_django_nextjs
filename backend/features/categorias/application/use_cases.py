"""
Casos de uso del slice `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Cada use case corresponde a un endpoint REST:

    Endpoint REST                             Use Case
    ─────────────────────────────────────────────────────────────
    GET    /api/categorias/                   ListarCategoriasUseCase
    GET    /api/categorias/<uuid>/            ObtenerCategoriaUseCase
    GET    /api/categorias/<uuid>/subcat...   ListarSubcategoriasUseCase
    POST   /api/categorias/                   CrearCategoriaUseCase
    PUT    /api/categorias/<uuid>/            ActualizarCategoriaUseCase
    DELETE /api/categorias/<uuid>/            EliminarCategoriaUseCase

LÓGICA DE JERARQUÍA:
    Los use cases de Crear y Actualizar validan que el parent_id
    (si no es None) exista. Además, el de Actualizar valida que no
    se cree un CICLO al cambiar el padre.

    La validación de ciclos:
        1. Si se intenta cambiar el parent de "A" a "B".
        2. Se obtienen los ancestros de "B" (padre, abuelo...).
        3. Si "A" está en esos ancestros → ciclo → 400.
════════════════════════════════════════════════════════════════════
"""

from uuid import UUID

from django.db.models import ProtectedError

from features.categorias.application.dtos import (
    CategoriaInputDTO,
    CategoriaOutputDTO,
)
from features.categorias.domain.entities import Categoria
from features.categorias.domain.repositories import CategoriaRepository
from features.categorias.domain.value_objects import NombreCategoria
from shared.domain.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)


def _to_dto(categoria: Categoria) -> CategoriaOutputDTO:
    """Convierte una entidad de dominio en DTO de salida."""
    return CategoriaOutputDTO(
        id=categoria.id,
        nombre=categoria.nombre,
        parent_id=categoria.parent_id,
        descripcion=categoria.descripcion,
    )


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Listar categorías
# API: GET /api/categorias/?search=&ordering=&only_roots=&parent=&page=
# ═══════════════════════════════════════════════════════════════════
class ListarCategoriasUseCase:
    """
    Lista categorías con filtros de jerarquía y paginación.

    API: la vista extrae los query params de `request.query_params`
    y los pasa. Soporta:
      - ?search=texto
      - ?ordering=nombre | -nombre | created_at | -created_at
      - ?only_roots=true (solo raíces)
      - ?parent=<uuid> (hijos directos de esa categoría)
      - ?page=N&page_size=M
    """

    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    def execute(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        only_roots: bool = False,
        parent_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[CategoriaOutputDTO], int]:
        """
        Ejecuta el listado.

        Args:
            search: `?search=texto`.
            ordering: `?ordering=nombre` (con `-` para descendente).
            only_roots: `?only_roots=true` → solo raíces.
            parent_id: `?parent=<uuid>` → hijos directos de esa.
            page: `?page=2` (1-based).
            page_size: `?page_size=20` (1-100).

        Returns:
            (lista de DTOs, total sin paginar)

        Raises:
            ValidationError: si page o page_size fuera de rango → 400.
        """
        if page < 1:
            raise ValidationError("page debe ser >= 1.", code="page_invalid")
        if page_size < 1 or page_size > 100:
            raise ValidationError(
                "page_size debe estar entre 1 y 100.",
                code="page_size_invalid",
            )

        offset = (page - 1) * page_size

        items, total = self._repo.list_all(
            search=search,
            ordering=ordering,
            parent_id=parent_id,
            only_roots=only_roots,
            offset=offset,
            limit=page_size,
        )
        return [_to_dto(c) for c in items], total


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Obtener una categoría por id
# API: GET /api/categorias/<uuid>/
# ═══════════════════════════════════════════════════════════════════
class ObtenerCategoriaUseCase:
    """
    Devuelve una categoría por UUID.

    API: si no existe → NotFoundError → 404.
    """

    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    def execute(self, categoria_id: UUID) -> CategoriaOutputDTO:
        categoria = self._repo.get_by_id(categoria_id)
        if categoria is None:
            raise NotFoundError(
                "Categoría no encontrada.",
                code="categoria_not_found",
            )
        return _to_dto(categoria)


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Listar subcategorías directas
# API: GET /api/categorias/<uuid>/subcategorias/
# ═══════════════════════════════════════════════════════════════════
class ListarSubcategoriasUseCase:
    """
    Devuelve los hijos directos de una categoría.

    API: endpoint extra que devuelve SOLO los hijos de primer nivel.
    No pagina (los hijos directos suelen ser pocos).

    Si la categoría padre no existe → 404.
    """

    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    def execute(self, parent_id: UUID) -> list[CategoriaOutputDTO]:
        # Primero comprobamos que el padre existe, para dar 404 en vez
        # de una lista vacía confusa.
        parent = self._repo.get_by_id(parent_id)
        if parent is None:
            raise NotFoundError(
                "Categoría padre no encontrada.",
                code="categoria_not_found",
            )

        children = self._repo.list_children(parent_id)
        return [_to_dto(c) for c in children]


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Crear categoría
# API: POST /api/categorias/
# ═══════════════════════════════════════════════════════════════════
class CrearCategoriaUseCase:
    """
    Crea una categoría nueva.

    API: POST /api/categorias/. Valida:
      - nombre no vacío y ≤150 chars (VO).
      - si parent_id != None, que exista esa categoría padre.

    Si el padre no existe → NotFoundError → 404.
    """

    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    def execute(self, dto: CategoriaInputDTO) -> CategoriaOutputDTO:
        # 1) Validar nombre (VO).
        nombre = NombreCategoria(dto.nombre).value

        # 2) Si hay parent_id, verificar que existe.
        if dto.parent_id is not None:
            parent = self._repo.get_by_id(dto.parent_id)
            if parent is None:
                raise NotFoundError(
                    "Categoría padre no encontrada.",
                    code="parent_not_found",
                )

        # 3) Crear.
        categoria = self._repo.create(
            nombre=nombre,
            parent_id=dto.parent_id,
            descripcion=(dto.descripcion or "").strip() or None,
        )
        return _to_dto(categoria)


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Actualizar categoría (con validación de CICLOS)
# API: PUT /api/categorias/<uuid>/
# ═══════════════════════════════════════════════════════════════════
class ActualizarCategoriaUseCase:
    """
    Actualiza una categoría existente.

    API: PUT /api/categorias/<uuid>/. Validaciones:
      - La categoría debe existir → 404 si no.
      - Nombre válido (VO) → 400 si no.
      - Si se cambia `parent_id`:
          * El nuevo padre debe existir → 404 si no.
          * El nuevo padre NO puede ser descendiente de la propia
            categoría → 400 (ciclo detectado).

    ⚠️ DETECCIÓN DE CICLOS (la parte crítica):
        Ejemplo:
            Ciencias → Física → Mecánica Cuántica
        Si intentas cambiar Ciencias.parent_id = Mecánica Cuántica.id,
        sería un ciclo (Ciencias dependería de su propio descendiente).

        Algoritmo:
            ancestros_del_nuevo_padre = repo.get_ancestor_ids(nuevo_parent_id)
            if categoria_id in ancestros_del_nuevo_padre:
                raise ValidationError("ciclo")
    """

    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    def execute(
        self,
        categoria_id: UUID,
        dto: CategoriaInputDTO,
        *,
        change_parent: bool = False,
    ) -> CategoriaOutputDTO:
        """
        Args:
            categoria_id: UUID de la categoría a actualizar.
            dto: nuevos datos.
            change_parent: si True, aplica `dto.parent_id` (incluso None).
                           Si False, mantiene el padre actual.

        Raises:
            NotFoundError: la categoría o el nuevo padre no existen → 404.
            ValidationError: nombre inválido o ciclo → 400.
        """
        # 1) Verificar que la categoría existe.
        existing = self._repo.get_by_id(categoria_id)
        if existing is None:
            raise NotFoundError(
                "Categoría no encontrada.",
                code="categoria_not_found",
            )

        # 2) Validar nombre (VO).
        nombre = NombreCategoria(dto.nombre).value

        # 3) Si se va a cambiar el padre, validar:
        if change_parent:
            new_parent_id = dto.parent_id

            # 3.1) Si nuevo padre != None, debe existir.
            if new_parent_id is not None:
                new_parent = self._repo.get_by_id(new_parent_id)
                if new_parent is None:
                    raise NotFoundError(
                        "Categoría padre no encontrada.",
                        code="parent_not_found",
                    )

                # 3.2) DETECCIÓN DE CICLO.
                #     Si categoria_id está entre los ancestros del nuevo padre,
                #     es un ciclo → error.
                ancestors = self._repo.get_ancestor_ids(new_parent_id)
                if categoria_id in ancestors:
                    raise ValidationError(
                        "No se puede asignar un padre que sea descendiente "
                        "de la propia categoría (se produciría un ciclo).",
                        code="categoria_ciclo",
                    )

        # 4) Persistir.
        categoria = self._repo.update(
            categoria_id,
            nombre=nombre,
            parent_id=dto.parent_id,
            change_parent=change_parent,
            descripcion=(dto.descripcion or "").strip() or None,
        )
        if categoria is None:
            # No debería pasar (ya lo comprobamos arriba), pero por seguridad.
            raise NotFoundError(
                "Categoría no encontrada.",
                code="categoria_not_found",
            )
        return _to_dto(categoria)


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Eliminar categoría
# API: DELETE /api/categorias/<uuid>/
# ═══════════════════════════════════════════════════════════════════
class EliminarCategoriaUseCase:
    """
    Elimina una categoría.

    API: DELETE /api/categorias/<uuid>/. Errores:
      - 404 si no existe.
      - 409 Conflict si tiene hijos (PROTECT).
    """

    def __init__(self, repo: CategoriaRepository) -> None:
        self._repo = repo

    def execute(self, categoria_id: UUID) -> None:
        try:
            deleted = self._repo.delete(categoria_id)
        except ProtectedError as exc:
            # ⚠️ PROTECT lanzado por Django → 409 Conflict.
            raise ConflictError(
                "No se puede eliminar una categoría que tiene subcategorías. "
                "Elimina primero sus subcategorías.",
                code="categoria_con_hijos",
            ) from exc

        if not deleted:
            raise NotFoundError(
                "Categoría no encontrada.",
                code="categoria_not_found",
            )
