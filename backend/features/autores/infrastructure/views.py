"""
Vistas HTTP del slice `autores`.
"""

from typing import Any
from uuid import UUID

from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from features.autores.application.dtos import AutorInputDTO
from features.autores.application.use_cases import (
    ActualizarAutorUseCase,
    CrearAutorUseCase,
    EliminarAutorUseCase,
    ListarAutoresUseCase,
    ObtenerAutorUseCase,
)
from features.autores.infrastructure.repositories import DjangoAutorRepository
from features.autores.infrastructure.serializers import (
    AutorInputSerializer,
    AutorOutputSerializer,
)


def _parse_int(value: str | None, default: int) -> int:
    """Parsea un int de querystring, o devuelve el default."""
    try:
        return int(value) if value else default
    except ValueError:
        return default


class AutoresListView(APIView):
    """
    GET  /api/autores/      → lista paginada
    POST /api/autores/      → crea autor
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Lista con ?search=, ?ordering=, ?page=, ?page_size=."""
        use_case = ListarAutoresUseCase(DjangoAutorRepository())
        page = _parse_int(request.query_params.get("page"), 1)
        page_size = _parse_int(request.query_params.get("page_size"), 20)
        autores, total = use_case.execute(
            search=request.query_params.get("search"),
            ordering=request.query_params.get("ordering"),
            page=page,
            page_size=page_size,
        )
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": AutorOutputSerializer(autores, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request: Request) -> Response:
        """Crea un autor (acepta multipart/form-data con foto)."""
        serializer = AutorInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = dict(serializer.validated_data)

        foto_file = data.pop("foto", None)
        foto_path: str | None = None
        if foto_file is not None:
            # Guarda la foto en MEDIA_ROOT con nombre UUID + extensión.
            extension = foto_file.name.rsplit(".", 1)[-1].lower()
            filename = f"autores/fotos/tmp_{extension}"
            saved_name = default_storage.save(filename, foto_file)
            foto_path = saved_name

        dto = AutorInputDTO(**data)
        autor = CrearAutorUseCase(DjangoAutorRepository()).execute(dto, foto=foto_path)
        return Response(AutorOutputSerializer(autor).data, status=status.HTTP_201_CREATED)


class AutorDetailView(APIView):
    """
    GET    /api/autores/<uuid>/  → detalle
    PUT    /api/autores/<uuid>/  → actualiza
    DELETE /api/autores/<uuid>/  → elimina
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, autor_id: UUID) -> Response:
        autor = ObtenerAutorUseCase(DjangoAutorRepository()).execute(autor_id)
        return Response(AutorOutputSerializer(autor).data)

    def put(self, request: Request, autor_id: UUID) -> Response:
        serializer = AutorInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data: dict[str, Any] = dict(serializer.validated_data)
        foto_file = data.pop("foto", None)
        foto_path: str | None = None
        if foto_file is not None:
            extension = foto_file.name.rsplit(".", 1)[-1].lower()
            filename = f"autores/fotos/tmp_{extension}"
            saved_name = default_storage.save(filename, foto_file)
            foto_path = saved_name

        dto = AutorInputDTO(**data)
        autor = ActualizarAutorUseCase(DjangoAutorRepository()).execute(
            autor_id, dto, foto=foto_path
        )
        return Response(AutorOutputSerializer(autor).data)

    def delete(self, request: Request, autor_id: UUID) -> Response:
        EliminarAutorUseCase(DjangoAutorRepository()).execute(autor_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
