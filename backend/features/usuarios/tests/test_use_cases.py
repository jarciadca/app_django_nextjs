from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from features.usuarios.application.dtos import RegistroInputDTO
from features.usuarios.application.use_cases import RegistrarUsuarioUseCase
from features.usuarios.domain.entities import Usuario
from shared.domain.exceptions import ValidationError


class FakeUsuarioRepository:
    """Repositorio en memoria para tests."""

    def __init__(self) -> None:
        self._by_id: dict[UUID, Usuario] = {}
        self._passwords: dict[UUID, str] = {}

    def get_by_id(self, user_id: UUID) -> Usuario | None:
        return self._by_id.get(user_id)

    def get_by_username(self, username: str) -> Usuario | None:
        for u in self._by_id.values():
            if u.username == username:
                return u
        return None

    def get_by_email(self, email: str) -> Usuario | None:
        for u in self._by_id.values():
            if u.email == email.lower():
                return u
        return None

    def exists_by_username(self, username: str) -> bool:
        return self.get_by_username(username) is not None

    def exists_by_email(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def create(
        self,
        *,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> Usuario:
        user_id = uuid4()
        usuario = Usuario(
            id=user_id,
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_staff=False,
            date_joined=datetime.now(UTC),
        )
        self._by_id[user_id] = usuario
        self._passwords[user_id] = password
        return usuario

    def set_password(self, user_id: UUID, new_password: str) -> None:
        self._passwords[user_id] = new_password


def test_registro_crea_usuario() -> None:
    repo = FakeUsuarioRepository()
    use_case = RegistrarUsuarioUseCase(repo)

    dto = RegistroInputDTO(
        username="pedro",
        email="pedro@example.com",
        password="password123",
    )
    out = use_case.execute(dto)

    assert out.username == "pedro"
    assert out.email == "pedro@example.com"


def test_registro_falla_si_username_existe() -> None:
    repo = FakeUsuarioRepository()
    use_case = RegistrarUsuarioUseCase(repo)
    dto = RegistroInputDTO(username="pedro", email="pedro@example.com", password="password123")
    use_case.execute(dto)

    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(
            RegistroInputDTO(
                username="pedro",
                email="otro@example.com",
                password="password123",
            )
        )

    assert exc_info.value.code == "username_taken"


def test_registro_falla_password_corta() -> None:
    repo = FakeUsuarioRepository()
    use_case = RegistrarUsuarioUseCase(repo)

    with pytest.raises(ValidationError) as exc_info:
        use_case.execute(
            RegistroInputDTO(username="pedro", email="pedro@example.com", password="123")
        )

    assert exc_info.value.code == "password_too_short"
