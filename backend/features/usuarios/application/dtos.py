"""
Data Transfer Objects (DTOs) del slice `usuarios`.

Los DTOs son objetos planos que transportan datos entre capas. Aíslan
la API pública de los casos de uso del formato interno (diccionarios,
modelos Django, etc.).

Regla: los DTOs viven en aplicación; los use cases reciben y devuelven DTOs.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegistroInputDTO:
    """Datos de entrada para registrar un usuario."""

    username: str
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""


@dataclass(frozen=True)
class UsuarioOutputDTO:
    """Datos de salida con la información pública de un usuario."""

    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool


@dataclass(frozen=True)
class LoginInputDTO:
    """Datos de entrada para login."""

    username: str
    password: str


@dataclass(frozen=True)
class TokensOutputDTO:
    """Tokens JWT devueltos al cliente."""

    access: str
    refresh: str


@dataclass(frozen=True)
class SolicitarResetInputDTO:
    """Datos de entrada para solicitar reset de contraseña."""

    email: str


@dataclass(frozen=True)
class ConfirmarResetInputDTO:
    """Datos de entrada para confirmar reset."""

    token: str
    new_password: str
