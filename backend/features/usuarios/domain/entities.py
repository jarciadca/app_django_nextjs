"""
Entidades del dominio `usuarios`.

Aquí viven los objetos de negocio puros, sin dependencias de Django.
Las entidades se usan en la capa de aplicación (casos de uso) y son
independientes del ORM.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Usuario:
    """
    Entidad de dominio que representa a un usuario.

    Es un dataclass inmutable (frozen=True): una vez creado, sus campos
    no se modifican. Para "cambiar" algo, se crea una nueva instancia con
    `dataclasses.replace()`.

    Attributes:
        id: UUID del usuario.
        username: identificador de login.
        email: email de contacto.
        first_name: nombre (opcional).
        last_name: apellidos (opcional).
        is_active: si puede autenticarse.
        is_staff: si puede entrar al admin.
        date_joined: fecha de alta.
    """

    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_staff: bool
    date_joined: datetime

    @property
    def full_name(self) -> str:
        """Nombre completo o username si no hay nombre."""
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username


@dataclass(frozen=True)
class PasswordResetTokenData:
    """
    Entidad de dominio que representa un token de reset de contraseña.

    Attributes:
        id: UUID del token.
        user_id: UUID del usuario propietario.
        token_hash: hash sha256 del token (nunca el token en claro).
        created_at: cuándo se creó.
        expires_at: cuándo caduca.
        used_at: cuándo se usó (None si no se ha usado).
    """

    id: UUID
    user_id: UUID
    token_hash: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None

    @property
    def is_usable(self) -> bool:
        """True si el token puede usarse (no expirado, no usado)."""
        from django.utils import timezone  # import local para no acoplar el módulo

        return self.used_at is None and timezone.now() <= self.expires_at
