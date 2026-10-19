"""
Tests de casos de uso de `autores` con repositorio fake.
"""

from uuid import UUID, uuid4

import pytest

from features.autores.application.dtos import AutorInputDTO
from features.autores.application.use_cases import (
    CrearAutorUseCase,
    ObtenerAutorUseCase,
)
from features.autores.domain.entities import Autor
from shared.domain.exceptions import NotFoundError, ValidationError


class FakeAutorRepository:
    def __init__(self) -> None:
        self._data: dict[UUID, Autor] = {}

    def list(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Autor], int]:
        items = list(self._data.values())
        return items[offset : offset + limit], len(items)

    def get_by_id(self, autor_id: UUID) -> Autor | None:
        return self._data.get(autor_id)

    def create(
        self,
        *,
        nombre: str,
        apellido: str,
        email: str,
        afiliacion: str,
        orcid: str | None,
        pais: str | None,
        bio: str | None,
        foto: str | None,
    ) -> Autor:
        autor = Autor(
            id=uuid4(),
            nombre=nombre,
            apellido=apellido,
            email=email,
            afiliacion=afiliacion,
            orcid=orcid,
            pais=pais,
            bio=bio,
            foto=foto,
        )
        self._data[autor.id] = autor
        return autor

    def update(
        self,
        autor_id: UUID,
        *,
        nombre: str | None = None,
        apellido: str | None = None,
        email: str | None = None,
        afiliacion: str | None = None,
        orcid: str | None = None,
        pais: str | None = None,
        bio: str | None = None,
        foto: str | None = None,
    ) -> Autor | None:
        current = self._data.get(autor_id)
        if current is None:
            return None
        updated = Autor(
            id=current.id,
            nombre=nombre if nombre is not None else current.nombre,
            apellido=apellido if apellido is not None else current.apellido,
            email=email if email is not None else current.email,
            afiliacion=afiliacion if afiliacion is not None else current.afiliacion,
            orcid=orcid if orcid is not None else current.orcid,
            pais=pais if pais is not None else current.pais,
            bio=bio if bio is not None else current.bio,
            foto=foto if foto is not None else current.foto,
        )
        self._data[autor_id] = updated
        return updated

    def delete(self, autor_id: UUID) -> bool:
        return self._data.pop(autor_id, None) is not None


def test_crear_autor_valido() -> None:
    repo = FakeAutorRepository()
    out = CrearAutorUseCase(repo).execute(
        AutorInputDTO(
            nombre="Ada",
            apellido="Lovelace",
            email="ada@example.com",
            afiliacion="UAM",
            orcid="0000-0002-1825-0097",
            pais="ES",
            bio="Pionera de la computación.",
        )
    )
    assert out.nombre == "Ada"
    assert out.orcid == "0000-0002-1825-0097"


def test_crear_autor_orcid_invalido() -> None:
    with pytest.raises(ValidationError):
        CrearAutorUseCase(FakeAutorRepository()).execute(
            AutorInputDTO(
                nombre="X",
                apellido="Y",
                email="x@example.com",
                orcid="123",
            )
        )


def test_obtener_autor_inexistente() -> None:
    with pytest.raises(NotFoundError):
        ObtenerAutorUseCase(FakeAutorRepository()).execute(uuid4())
