"""
Vistas HTTP del slice `revistas`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Una vista (APIView de DRF) es el ADAPTADOR entre HTTP y los casos de uso.
Su única responsabilidad: leer request → invocar use case → construir Response.

NO contiene lógica de negocio. Las reglas (checksum ISSN, unicidad,
validaciones) viven en el use case y en el dominio.

Endpoints servidos por este archivo:
    GET    /api/revistas/              → RevistasListView.get
    POST   /api/revistas/              → RevistasListView.post
    GET    /api/revistas/<uuid>/       → RevistaDetailView.get
    PUT    /api/revistas/<uuid>/       → RevistaDetailView.put
    DELETE /api/revistas/<uuid>/       → RevistaDetailView.delete

Autenticación: TODOS los endpoints requieren JWT válido
(`permission_classes = [IsAuthenticated]`). Sin token → 401
(manejado automáticamente por DRF, no por nuestro código).

Excepciones de dominio (`NotFoundError`, `ConflictError`,
`ValidationError`): se propagan al handler global que las traduce
a 401/404/409/400 problem+json. La vista NO las captura.
════════════════════════════════════════════════════════════════════
"""

# `UUID` para tipar el path param `<uuid:revista_id>`.
from uuid import UUID

# `status` contiene constantes HTTP (200, 201, 204, ...).
from rest_framework import status

# `IsAuthenticated`: el endpoint requiere JWT válido.
# API: sin `Authorization: Bearer <token>` → 401.
from rest_framework.permissions import IsAuthenticated

# `Request` es el tipo del request DRF (extends django.http.HttpRequest).
from rest_framework.request import Request

# `Response` construye la respuesta HTTP a partir de un dict/lista (se serializa a JSON).
from rest_framework.response import Response

# `APIView` es la clase base de DRF para vistas explícitas.
from rest_framework.views import APIView

# DTO de entrada.
from features.revistas.application.dtos import RevistaInputDTO

# Casos de uso.
from features.revistas.application.use_cases import (
    ActualizarRevistaUseCase,
    CrearRevistaUseCase,
    EliminarRevistaUseCase,
    ListarRevistasUseCase,
    ObtenerRevistaUseCase,
)

# Implementación concreta del repositorio (Django ORM).
# API: se instancia nueva por request (es barato, solo envuelve un queryset).
from features.revistas.infrastructure.repositories import DjangoRevistaRepository

# Serializers (input para validar forma, output para serializar la respuesta).
from features.revistas.infrastructure.serializers import (
    RevistaInputSerializer,
    RevistaOutputSerializer,
)


def _parse_int(value: str | None, default: int) -> int:
    """
    Parsea un entero de query string, con fallback al default.

    API: usado para `?page=` y `?page_size=`. Si el cliente envía
    `?page=abc`, devolvemos el default (1) y el use case validará
    rangos. Así no explotamos con ValueError por un query param basura.
    """
    try:
        return int(value) if value else default
    except ValueError:
        return default


class RevistasListView(APIView):
    """
    Endpoint de colección de revistas.

    API:
        GET  /api/revistas/  → lista paginada
        POST /api/revistas/  → crea una nueva revista
    """

    # API: sin JWT válido → 401 antes de ejecutar el método.
    permission_classes = [IsAuthenticated]

    # ═══════════════════════════════════════════════════════════════
    # GET /api/revistas/?search=&ordering=&page=&page_size=
    # ═══════════════════════════════════════════════════════════════
    def get(self, request: Request) -> Response:
        """
        Lista revistas con filtros.

        Query params:
            search: búsqueda libre en nombre/issn/editorial.
            ordering: campo (con `-` para descendente).
            page: número de página (1-based).
            page_size: tamaño de página (1-100).

        Respuesta JSON:
            {
              "count": 42,
              "page": 1,
              "page_size": 20,
              "results": [{"id": "...", "nombre": "...", ...}, ...]
            }

        Errores:
            400 → page o page_size fuera de rango (ValidationError del use case).
            401 → sin JWT válido (gestionado por DRF).
        """
        # Instanciamos el repo y el caso de uso por request.
        use_case = ListarRevistasUseCase(DjangoRevistaRepository())

        # Extraemos query params (siempre strings, o None si no vienen).
        page = _parse_int(request.query_params.get("page"), 1)
        page_size = _parse_int(request.query_params.get("page_size"), 20)

        # Ejecutamos. Puede lanzar ValidationError → handler global → 400.
        items, total = use_case.execute(
            search=request.query_params.get("search"),
            ordering=request.query_params.get("ordering"),
            page=page,
            page_size=page_size,
        )

        # Construimos el JSON paginado.
        # `many=True` indica al serializer que `items` es una lista de DTOs.
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": RevistaOutputSerializer(items, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    # ═══════════════════════════════════════════════════════════════
    # POST /api/revistas/
    # ═══════════════════════════════════════════════════════════════
    def post(self, request: Request) -> Response:
        """
        Crea una revista nueva.

        Body esperado (JSON):
            {
              "nombre": "Nature",
              "issn": "0028-0836",
              "editorial": "Springer",     ← opcional
              "pais": "GB",                ← opcional
              "sitio_web": "https://..."   ← opcional
            }

        Respuesta (201):
            {"id": "...", "nombre": "...", "issn": "...", ...}

        Errores:
            400 → forma inválida (serializer) o ISSN con checksum inválido (use case).
            401 → sin JWT.
            409 → ISSN ya existe (ConflictError del use case).
        """
        # 1) Validar FORMA del JSON.
        #    Si falta un campo obligatorio o un tipo no cuadra, DRF lanza
        #    ValidationError (de DRF) → handler global → 400 problem+json.
        serializer = RevistaInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2) Construir DTO con los datos validados.
        dto = RevistaInputDTO(**serializer.validated_data)

        # 3) Ejecutar el caso de uso.
        #    Puede lanzar:
        #      - ValidationError (ISSN inválido, nombre vacío) → 400.
        #      - ConflictError (ISSN duplicado) → 409.
        revista_dto = CrearRevistaUseCase(DjangoRevistaRepository()).execute(dto)

        # 4) Serializar DTO → JSON y devolver con código 201 Created.
        return Response(
            RevistaOutputSerializer(revista_dto).data,
            status=status.HTTP_201_CREATED,
        )


class RevistaDetailView(APIView):
    """
    Endpoint de un recurso individual.

    API:
        GET    /api/revistas/<uuid>/  → detalle
        PUT    /api/revistas/<uuid>/  → actualiza
        DELETE /api/revistas/<uuid>/  → elimina
    """

    permission_classes = [IsAuthenticated]

    # ═══════════════════════════════════════════════════════════════
    # GET /api/revistas/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def get(self, request: Request, revista_id: UUID) -> Response:
        """
        Devuelve el detalle de una revista.

        Respuesta (200):
            {"id": "...", "nombre": "...", ...}

        Errores:
            401 → sin JWT.
            404 → revista no existe (NotFoundError del use case).
        """
        revista = ObtenerRevistaUseCase(DjangoRevistaRepository()).execute(revista_id)
        return Response(RevistaOutputSerializer(revista).data, status=status.HTTP_200_OK)

    # ═══════════════════════════════════════════════════════════════
    # PUT /api/revistas/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def put(self, request: Request, revista_id: UUID) -> Response:
        """
        Actualiza una revista existente.

        Body esperado: mismo que POST (todos los campos del recurso).

        Respuesta (200):
            {"id": "...", "nombre": "...", ...}

        Errores:
            400 → forma inválida o ISSN inválido.
            401 → sin JWT.
            404 → revista no existe.
            409 → nuevo ISSN ya pertenece a OTRA revista.
        """
        # 1) Validar forma.
        serializer = RevistaInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2) Construir DTO.
        dto = RevistaInputDTO(**serializer.validated_data)

        # 3) Ejecutar.
        #    El use case valida el ISSN con exclude_id=revista_id, así que
        #    no da un falso 409 cuando actualizas sin cambiar el ISSN.
        revista_dto = ActualizarRevistaUseCase(DjangoRevistaRepository()).execute(revista_id, dto)

        return Response(RevistaOutputSerializer(revista_dto).data, status=status.HTTP_200_OK)

    # ═══════════════════════════════════════════════════════════════
    # DELETE /api/revistas/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def delete(self, request: Request, revista_id: UUID) -> Response:
        """
        Elimina una revista.

        Respuesta (204):
            (sin body)

        Errores:
            401 → sin JWT.
            404 → revista no existe.
            409 → (Fase 4c) si hay artículos con FK a esta revista, se
                  devolverá 409 en vez de 500 (pendiente de añadir mapeo
                  de ProtectedError en el handler global).
        """
        EliminarRevistaUseCase(DjangoRevistaRepository()).execute(revista_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
