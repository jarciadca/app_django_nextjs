"""
Casos de uso del slice `autores`.
"""

from uuid import UUID

from features.autores.application.dtos import AutorInputDTO, AutorOutputDTO
from features.autores.domain.entities import Autor
from features.autores.domain.repositories import AutorRepository
from features.autores.domain.value_objects import NombreAutor, Orcid, Pais
from shared.domain.exceptions import NotFoundError, ValidationError


def _to_output_dto(autor: Autor) -> AutorOutputDTO:
    return AutorOutputDTO(
        id=autor.id,
        nombre=autor.nombre,
        apellido=autor.apellido,
        email=autor.email,
        afiliacion=autor.afiliacion,
        orcid=autor.orcid,
        pais=autor.pais,
        bio=autor.bio,
        foto=autor.foto,
    )


class ListarAutoresUseCase:
    """Lista autores con paginación, búsqueda y orden."""

    def __init__(self, repo: AutorRepository) -> None:
        self._repo = repo

    def execute(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AutorOutputDTO], int]:
        """
        Args:
            search: término de búsqueda libre.
            ordering: campo y dirección, ej. "-apellido".
            page: número de página (1-based).
            page_size: tamaño de página.

        Returns:
            (lista de autores, total sin paginar)
        """
        if page < 1:
            raise ValidationError("page debe ser >= 1.", code="page_invalid")
        if page_size < 1 or page_size > 100:
            raise ValidationError("page_size debe estar entre 1 y 100.", code="page_size_invalid")

        offset = (page - 1) * page_size
        autores, total = self._repo.list(
            search=search,
            ordering=ordering,
            offset=offset,
            limit=page_size,
        )
        return [_to_output_dto(a) for a in autores], total


class ObtenerAutorUseCase:
    """Devuelve un autor por id."""

    def __init__(self, repo: AutorRepository) -> None:
        self._repo = repo

    def execute(self, autor_id: UUID) -> AutorOutputDTO:
        autor = self._repo.get_by_id(autor_id)
        if autor is None:
            raise NotFoundError("Autor no encontrado.", code="autor_not_found")
        return _to_output_dto(autor)


class CrearAutorUseCase:
    """Crea un autor."""

    def __init__(self, repo: AutorRepository) -> None:
        self._repo = repo

    def execute(self, dto: AutorInputDTO, foto: str | None = None) -> AutorOutputDTO:
        # Validación con value objects.
        nombre = NombreAutor(dto.nombre, "nombre").value
        apellido = NombreAutor(dto.apellido, "apellido").value
        orcid = Orcid(dto.orcid).value
        pais = Pais(dto.pais).value

        autor = self._repo.create(
            nombre=nombre,
            apellido=apellido,
            email=dto.email.strip().lower(),
            afiliacion=dto.afiliacion.strip(),
            orcid=orcid,
            pais=pais,
            bio=(dto.bio or "").strip() or None,
            foto=foto,
        )
        return _to_output_dto(autor)


class ActualizarAutorUseCase:
    """Actualiza un autor (parcial o completo)."""

    def __init__(self, repo: AutorRepository) -> None:
        self._repo = repo

    def execute(
        self,
        autor_id: UUID,
        dto: AutorInputDTO,
        foto: str | None = None,
    ) -> AutorOutputDTO:
        nombre = NombreAutor(dto.nombre, "nombre").value
        apellido = NombreAutor(dto.apellido, "apellido").value
        orcid = Orcid(dto.orcid).value
        pais = Pais(dto.pais).value

        autor = self._repo.update(
            autor_id,
            nombre=nombre,
            apellido=apellido,
            email=dto.email.strip().lower(),
            afiliacion=dto.afiliacion.strip(),
            orcid=orcid,
            pais=pais,
            bio=(dto.bio or "").strip() or None,
            foto=foto,
        )
        if autor is None:
            raise NotFoundError("Autor no encontrado.", code="autor_not_found")
        return _to_output_dto(autor)


class EliminarAutorUseCase:
    """Elimina un autor."""

    def __init__(self, repo: AutorRepository) -> None:
        self._repo = repo

    def execute(self, autor_id: UUID) -> None:
        deleted = self._repo.delete(autor_id)
        if not deleted:
            raise NotFoundError("Autor no encontrado.", code="autor_not_found")
