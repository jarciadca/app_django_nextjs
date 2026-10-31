"""
Vistas HTTP del slice `articulos` (Fase 4c.1).

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Endpoints servidos por este archivo:
    GET    /api/articulos/              → lista con filtros
    POST   /api/articulos/              → crear
    GET    /api/articulos/<uuid>/       → detalle
    PUT    /api/articulos/<uuid>/       → actualizar
    DELETE /api/articulos/<uuid>/       → eliminar

Todos requieren JWT (`IsAuthenticated`). Las excepciones de dominio
(NotFoundError, ValidationError, ConflictError) suben al handler global
y se traducen a 404/400/409 problem+json.

En esta fase NO existen todavía:
  - Endpoints de autores (/api/articulos/<uuid>/autores/).
  - Endpoints de categorías (/api/articulos/<uuid>/categorias/).
  - Endpoints de publicar/despublicar.
  - Subida de PDF.
  Esos llegan en Fase 4c.2 y 4c.3.
════════════════════════════════════════════════════════════════════
"""

from uuid import UUID

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from features.articulos.application.dtos import ArticuloInputDTO
from features.articulos.application.use_cases import (
    ActualizarArticuloUseCase,
    CrearArticuloUseCase,
    EliminarArticuloUseCase,
    ListarArticulosUseCase,
    ObtenerArticuloUseCase,
)
from features.articulos.infrastructure.repositories import DjangoArticuloRepository
from features.articulos.infrastructure.serializers import (
    ArticuloInputSerializer,
    ArticuloOutputSerializer,
)


def _parse_int(value: str | None, default: int) -> int:
    """Parsea un entero de query string con fallback al default."""
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _parse_int_or_none(value: str | None) -> int | None:
    """Parsea un entero opcional de query string. Devuelve None si vacío."""
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_uuid(value: str | None) -> UUID | None:
    """Parsea un UUID opcional de query string. Devuelve None si vacío o inválido."""
    if not value:
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


class ArticulosListView(APIView):
    """
    Endpoint de colección de artículos.

    API:
        GET  /api/articulos/  → lista con filtros
        POST /api/articulos/  → crear
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Lista artículos con filtros.

        Query params:
            search: búsqueda en título, resumen, palabras clave.
            estado: "borrador" | "publicado".
            revista: UUID de revista.
            anio: año exacto.
            anio_min / anio_max: rango de años.
            idioma: código ISO 639-1.
            ordering: "titulo" | "-anio" | "fecha_publicacion" | "-created_at".
            page / page_size: paginación.

        Respuesta:
            {
              "count": 42,
              "page": 1,
              "page_size": 20,
              "results": [{...}, ...]
            }
        """
        use_case = ListarArticulosUseCase(DjangoArticuloRepository())

        page = _parse_int(request.query_params.get("page"), 1)
        page_size = _parse_int(request.query_params.get("page_size"), 20)

        items, total = use_case.execute(
            search=request.query_params.get("search"),
            estado=request.query_params.get("estado"),
            revista_id=_parse_uuid(request.query_params.get("revista")),
            anio=_parse_int_or_none(request.query_params.get("anio")),
            anio_min=_parse_int_or_none(request.query_params.get("anio_min")),
            anio_max=_parse_int_or_none(request.query_params.get("anio_max")),
            idioma=request.query_params.get("idioma"),
            ordering=request.query_params.get("ordering"),
            page=page,
            page_size=page_size,
        )
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": ArticuloOutputSerializer(items, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request: Request) -> Response:
        """
        Crea un artículo nuevo.

        Body esperado:
            {
              "titulo": "Quantum entanglement in graphene",
              "anio": 2024,
              "revista_id": "uuid",
              "resumen": "...",           ← opcional
              "palabras_clave": "a,b,c",  ← opcional
              "doi": "10.1038/...",       ← opcional
              "idioma": "en",             ← opcional, default "es"
              "estado": "borrador",       ← opcional, default "borrador"
              "fecha_publicacion": "2024-05-01"  ← opcional
            }

        Errores:
            400 → validación (título vacío, año fuera de rango, DOI inválido...).
            401 → sin JWT.
            409 → DOI duplicado.
        """
        serializer = ArticuloInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = ArticuloInputDTO(**serializer.validated_data)
        articulo = CrearArticuloUseCase(DjangoArticuloRepository()).execute(dto)

        return Response(
            ArticuloOutputSerializer(articulo).data,
            status=status.HTTP_201_CREATED,
        )


class ArticuloDetailView(APIView):
    """
    Endpoint de un artículo individual.

    API:
        GET    /api/articulos/<uuid>/  → detalle
        PUT    /api/articulos/<uuid>/  → actualizar
        DELETE /api/articulos/<uuid>/  → eliminar
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, articulo_id: UUID) -> Response:
        """Devuelve el detalle de un artículo."""
        articulo = ObtenerArticuloUseCase(DjangoArticuloRepository()).execute(articulo_id)
        return Response(ArticuloOutputSerializer(articulo).data)

    def put(self, request: Request, articulo_id: UUID) -> Response:
        """
        Actualiza un artículo existente.

        Body: mismo que POST (todos los campos del recurso).

        Errores:
            400 → validación.
            401 → sin JWT.
            404 → artículo no existe.
            409 → DOI duplicado en OTRO artículo.
        """
        serializer = ArticuloInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = ArticuloInputDTO(**serializer.validated_data)
        articulo = ActualizarArticuloUseCase(DjangoArticuloRepository()).execute(articulo_id, dto)
        return Response(ArticuloOutputSerializer(articulo).data)

    def delete(self, request: Request, articulo_id: UUID) -> Response:
        """
        Elimina un artículo.

        Errores:
            401 → sin JWT.
            404 → artículo no existe.
            409 → (futuro) si tiene citas que lo referencian.
        """
        EliminarArticuloUseCase(DjangoArticuloRepository()).execute(articulo_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
