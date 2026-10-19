"""
Interfaces (puertos) de repositorios del dominio `usuarios`.

Un repositorio es una abstracción que oculta la persistencia. El dominio
solo conoce la INTERFAZ; la implementación (Django ORM, en memoria, fake)
vive en infraestructura.

Esto permite:
  - Testear casos de uso con un repositorio fake sin tocar la BD.
  - Cambiar el ORM sin tocar dominio ni aplicación.

Las interfaces usan `Protocol` para tipado estructural (duck typing).
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from features.usuarios.domain.entities import PasswordResetTokenData, Usuario


class UsuarioRepository(Protocol):
    """Interfaz del repositorio de usuarios."""

    def get_by_id(self, user_id: UUID) -> Usuario | None:
        """Devuelve el usuario con ese id, o None si no existe."""
        ...

    def get_by_username(self, username: str) -> Usuario | None:
        """Devuelve el usuario con ese username, o None si no existe."""
        ...

    def get_by_email(self, email: str) -> Usuario | None:
        """Devuelve el usuario con ese email, o None si no existe."""
        ...

    def exists_by_username(self, username: str) -> bool:
        """True si existe un usuario con ese username."""
        ...

    def exists_by_email(self, email: str) -> bool:
        """True si existe un usuario con ese email."""
        ...

    def create(
        self,
        *,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> Usuario:
        """Crea un usuario y lo persiste. Devuelve la entidad creada."""
        ...

    def set_password(self, user_id: UUID, new_password: str) -> None:
        """Cambia la contraseña de un usuario (hasheada)."""
        ...


class PasswordResetTokenRepository(Protocol):
    """Interfaz del repositorio de tokens de reset de contraseña."""

    def create(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        """Guarda un nuevo token de reset (hash)."""
        ...

    def get_by_hash(self, token_hash: str) -> PasswordResetTokenData | None:
        """Devuelve los datos del token por su hash, o None."""
        ...

    def mark_as_used(self, token_hash: str) -> None:
        """Marca el token como usado (no reutilizable)."""
        ...

    def invalidate_all_for_user(self, user_id: UUID) -> None:
        """Invalida (marca como usados) todos los tokens vigentes del usuario."""
        ...
