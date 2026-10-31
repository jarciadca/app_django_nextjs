"""
Casos de uso del slice `articulos` (Fase 4c.1).

Endpoints REST servidos:
    GET    /api/articulos/              → ListarArticulosUseCase
    GET    /api/articulos/<uuid>/       → ObtenerArticuloUseCase
    POST   /api/articulos/              → CrearArticuloUseCase
    PUT    /api/articulos/<uuid>/       → ActualizarArticuloUseCase
    DELETE /api/articulos/<uuid>/       → EliminarArticuloUseCase
"""

from uuid import UUID

from features.articulos.application.dtos import (
    ArticuloInputDTO,
    ArticuloOutputDTO,
)
from features.articulos.domain.entities import Articulo
from features.articulos.domain.repositories import ArticuloRepository
from features.articulos.domain.value_objects import (
    DOI,
    Anio,
    EstadoArticulo,
    Idioma,
    Titulo,
)
from shared.domain.exceptions import ConflictError, NotFoundError, ValidationError


def _to_dto(articulo: Articulo) -> ArticuloOutputDTO:
    return ArticuloOutputDTO(
        id=articulo.id,
        titulo=articulo.titulo,
        resumen=articulo.resumen,
        palabras_clave=articulo.palabras_clave,
        doi=articulo.doi,
        anio=articulo.anio,
        idioma=articulo.idioma,
        estado=articulo.estado,
        fecha_publicacion=articulo.fecha_publicacion,
        revista_id=articulo.revista_id,
    )


class ListarArticulosUseCase:
    """Lista artículos con filtros."""

    def __init__(self, repo: ArticuloRepository) -> None:
        self._repo = repo

    def execute(
        self,
        *,
        search: str | None = None,
        estado: str | None = None,
        revista_id: UUID | None = None,
        anio: int | None = None,
        anio_min: int | None = None,
        anio_max: int | None = None,
        idioma: str | None = None,
        ordering: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ArticuloOutputDTO], int]:
        if page < 1:
            raise ValidationError("page debe ser >= 1.", code="page_invalid")
        if page_size < 1 or page_size > 100:
            raise ValidationError("page_size debe estar entre 1 y 100.", code="page_size_invalid")

        items, total = self._repo.list_all(
            search=search,
            estado=estado,
            revista_id=revista_id,
            anio=anio,
            anio_min=anio_min,
            anio_max=anio_max,
            idioma=idioma,
            ordering=ordering,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return [_to_dto(a) for a in items], total


class ObtenerArticuloUseCase:
    """Obtiene un artículo por UUID."""

    def __init__(self, repo: ArticuloRepository) -> None:
        self._repo = repo

    def execute(self, articulo_id: UUID) -> ArticuloOutputDTO:
        articulo = self._repo.get_by_id(articulo_id)
        if articulo is None:
            raise NotFoundError("Artículo no encontrado.", code="articulo_not_found")
        return _to_dto(articulo)


class CrearArticuloUseCase:
    """Crea un artículo nuevo."""

    def __init__(self, repo: ArticuloRepository) -> None:
        self._repo = repo

    def execute(self, dto: ArticuloInputDTO) -> ArticuloOutputDTO:
        # Validaciones con VOs.
        titulo = Titulo(dto.titulo).value
        anio = Anio(dto.anio).value
        idioma = Idioma(dto.idioma).value
        estado = EstadoArticulo(dto.estado).value
        doi = DOI(dto.doi).value

        # Unicidad de DOI si existe.
        if doi is not None and self._repo.exists_by_doi(doi):
            raise ConflictError("Ya existe un artículo con ese DOI.", code="doi_taken")

        # Normalizar palabras clave (trim y dedupe por coma).
        palabras_clave = dto.palabras_clave.strip()

        articulo = self._repo.create(
            titulo=titulo,
            resumen=dto.resumen.strip(),
            palabras_clave=palabras_clave,
            doi=doi,
            anio=anio,
            idioma=idioma,
            estado=estado,
            fecha_publicacion=dto.fecha_publicacion,
            revista_id=dto.revista_id,
        )
        return _to_dto(articulo)


class ActualizarArticuloUseCase:
    """Actualiza un artículo."""

    def __init__(self, repo: ArticuloRepository) -> None:
        self._repo = repo

    def execute(self, articulo_id: UUID, dto: ArticuloInputDTO) -> ArticuloOutputDTO:
        titulo = Titulo(dto.titulo).value
        anio = Anio(dto.anio).value
        idioma = Idioma(dto.idioma).value
        estado = EstadoArticulo(dto.estado).value
        doi = DOI(dto.doi).value

        if doi is not None and self._repo.exists_by_doi(doi, exclude_id=articulo_id):
            raise ConflictError("Ya existe OTRO artículo con ese DOI.", code="doi_taken")

        articulo = self._repo.update(
            articulo_id,
            titulo=titulo,
            resumen=dto.resumen.strip(),
            palabras_clave=dto.palabras_clave.strip(),
            doi=doi,
            anio=anio,
            idioma=idioma,
            estado=estado,
            fecha_publicacion=dto.fecha_publicacion,
            revista_id=dto.revista_id,
        )
        if articulo is None:
            raise NotFoundError("Artículo no encontrado.", code="articulo_not_found")
        return _to_dto(articulo)


class EliminarArticuloUseCase:
    """Elimina un artículo."""

    def __init__(self, repo: ArticuloRepository) -> None:
        self._repo = repo

    def execute(self, articulo_id: UUID) -> None:
        if not self._repo.delete(articulo_id):
            raise NotFoundError("Artículo no encontrado.", code="articulo_not_found")
