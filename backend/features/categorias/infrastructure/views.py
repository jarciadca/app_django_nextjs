"""
Vistas HTTP del slice `categorias`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Endpoints servidos por este archivo:
    GET    /api/categorias/                              → lista
    POST   /api/categorias/                              → crear
    GET    /api/categorias/<uuid>/                       → detalle
    PUT    /api/categorias/<uuid>/                       → actualizar
    DELETE /api/categorias/<uuid>/                       → eliminar
    GET    /api/categorias/<uuid>/subcategorias/         → hijos directos

Todos requieren JWT (`IsAuthenticated`). Las excepciones de dominio
(NotFoundError, ValidationError, ConflictError) suben al handler global
y se traducen a 404/400/409 problem+json.

El endpoint `/subcategorias/` es especial: en vez de estar en
`CategoriaDetailView` con otra acción, tiene su propia vista para
mantener una responsabilidad por clase.
════════════════════════════════════════════════════════════════════
"""

from uuid import UUID

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from features.categorias.application.dtos import CategoriaInputDTO
from features.categorias.application.use_cases import (
    ActualizarCategoriaUseCase,
    CrearCategoriaUseCase,
    EliminarCategoriaUseCase,
    ListarCategoriasUseCase,
    ListarSubcategoriasUseCase,
    ObtenerCategoriaUseCase,
)
from features.categorias.infrastructure.repositories import DjangoCategoriaRepository
from features.categorias.infrastructure.serializers import (
    CategoriaInputSerializer,
    CategoriaOutputSerializer,
)


def _parse_int(value: str | None, default: int) -> int:
    """Parsea entero de query string con fallback al default."""
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _parse_bool(value: str | None) -> bool:
    """
    Parsea booleano de query string.

    Acepta: "true", "1", "yes" (case-insensitive) → True.
    Cualquier otra cosa → False.
    """
    if value is None:
        return False
    return value.strip().lower() in {"true", "1", "yes"}


class CategoriasListView(APIView):
    """
    Endpoint de colección de categorías.

    API:
        GET  /api/categorias/  → lista con filtros
        POST /api/categorias/  → crear
    """

    permission_classes = [IsAuthenticated]

    # ═══════════════════════════════════════════════════════════════
    # GET /api/categorias/?search=&ordering=&only_roots=&parent=&page=&page_size=
    # ═══════════════════════════════════════════════════════════════
    def get(self, request: Request) -> Response:
        """
        Lista categorías con filtros de jerarquía.

        Query params:
            search: búsqueda en nombre/descripción.
            ordering: campo (con `-` para descendente).
            only_roots: `true` → solo raíces.
            parent: UUID → hijos directos de esa categoría.
            page: número de página.
            page_size: tamaño de página (1-100).

        Respuesta JSON:
            {
              "count": 12,
              "page": 1,
              "page_size": 20,
              "results": [{"id": "...", "parent_id": "...", ...}]
            }
        """
        use_case = ListarCategoriasUseCase(DjangoCategoriaRepository())

        page = _parse_int(request.query_params.get("page"), 1)
        page_size = _parse_int(request.query_params.get("page_size"), 20)
        only_roots = _parse_bool(request.query_params.get("only_roots"))

        # `parent` como UUID (o None si no viene / está mal formado).
        parent_id: UUID | None = None
        parent_raw = request.query_params.get("parent")
        if parent_raw:
            try:
                parent_id = UUID(parent_raw)
            except ValueError:
                # Si es un UUID inválido, lo ignoramos (mejor que un 500).
                parent_id = None

        items, total = use_case.execute(
            search=request.query_params.get("search"),
            ordering=request.query_params.get("ordering"),
            only_roots=only_roots,
            parent_id=parent_id,
            page=page,
            page_size=page_size,
        )

        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": CategoriaOutputSerializer(items, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    # ═══════════════════════════════════════════════════════════════
    # POST /api/categorias/
    # ═══════════════════════════════════════════════════════════════
    def post(self, request: Request) -> Response:
        """
        Crea una categoría.

        Body:
            {"nombre": "Física", "parent_id": "uuid-o-null", "descripcion": "..."}

        Errores:
            400 → nombre inválido.
            401 → sin JWT.
            404 → parent_id apunta a una categoría que no existe.
        """
        serializer = CategoriaInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = CategoriaInputDTO(**serializer.validated_data)
        categoria = CrearCategoriaUseCase(DjangoCategoriaRepository()).execute(dto)

        return Response(
            CategoriaOutputSerializer(categoria).data,
            status=status.HTTP_201_CREATED,
        )


class CategoriaDetailView(APIView):
    """
    Endpoint de un recurso individual.

    API:
        GET    /api/categorias/<uuid>/  → detalle
        PUT    /api/categorias/<uuid>/  → actualizar
        DELETE /api/categorias/<uuid>/  → eliminar
    """

    permission_classes = [IsAuthenticated]

    # ═══════════════════════════════════════════════════════════════
    # GET /api/categorias/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def get(self, request: Request, categoria_id: UUID) -> Response:
        """Devuelve el detalle de una categoría."""
        categoria = ObtenerCategoriaUseCase(DjangoCategoriaRepository()).execute(categoria_id)
        return Response(CategoriaOutputSerializer(categoria).data)

    # ═══════════════════════════════════════════════════════════════
    # PUT /api/categorias/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def put(self, request: Request, categoria_id: UUID) -> Response:
        """
        Actualiza una categoría.

        Body: mismo que POST.

        Nota sobre `parent_id`:
            - Si el body INCLUYE la clave `parent_id` (aunque sea null),
              se interpreta como "cambiar el padre a ese valor" (o a raíz
              si es null). `change_parent=True`.
            - Si el body NO incluye la clave `parent_id`, se mantiene el
              padre actual. `change_parent=False`.

        Errores:
            400 → nombre inválido o ciclo detectado.
            401 → sin JWT.
            404 → la categoría o el nuevo padre no existen.
        """
        serializer = CategoriaInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = CategoriaInputDTO(**serializer.validated_data)

        # Detectamos si el cliente intenta cambiar el padre.
        # Si la clave `parent_id` está en el body, aunque sea `null`,
        # significa "cambiar el parent a lo que indique".
        change_parent = "parent_id" in request.data

        categoria = ActualizarCategoriaUseCase(DjangoCategoriaRepository()).execute(
            categoria_id,
            dto,
            change_parent=change_parent,
        )

        return Response(CategoriaOutputSerializer(categoria).data)

    # ═══════════════════════════════════════════════════════════════
    # DELETE /api/categorias/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def delete(self, request: Request, categoria_id: UUID) -> Response:
        """
        Elimina una categoría.

        Errores:
            401 → sin JWT.
            404 → no existe.
            409 → tiene subcategorías (PROTECT).
        """
        EliminarCategoriaUseCase(DjangoCategoriaRepository()).execute(categoria_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoriaSubcategoriasView(APIView):
    """
    Endpoint extra para listar hijos directos.

    API: GET /api/categorias/<uuid>/subcategorias/

    Devuelve SOLO los hijos de primer nivel (no recursivo).
    Respuesta: lista plana (sin paginación).
        {
          "parent_id": "uuid",
          "count": 2,
          "results": [{"id": "...", "nombre": "...", ...}, ...]
        }

    Errores:
        401 → sin JWT.
        404 → la categoría padre no existe.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, categoria_id: UUID) -> Response:
        """Devuelve los hijos directos de una categoría."""
        children = ListarSubcategoriasUseCase(DjangoCategoriaRepository()).execute(categoria_id)
        return Response(
            {
                "parent_id": str(categoria_id),
                "count": len(children),
                "results": CategoriaOutputSerializer(children, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
