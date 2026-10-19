"""
Casos de uso del slice `usuarios`.

Cada caso de uso es una clase con un método `execute()` que orquesta
el dominio y los repositorios para cumplir un objetivo de negocio.

Reglas:
  - No importan Django (salvo concesiones pragmáticas marcadas).
  - Reciben DTOs, devuelven DTOs o entidades.
  - Lanzan excepciones de dominio (ValidationError, NotFoundError, …).
"""

import contextlib
import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from features.usuarios.application.dtos import (
    LoginInputDTO,
    RegistroInputDTO,
    TokensOutputDTO,
    UsuarioOutputDTO,
)
from features.usuarios.domain.entities import Usuario
from features.usuarios.domain.repositories import (
    PasswordResetTokenRepository,
    UsuarioRepository,
)
from features.usuarios.domain.value_objects import Email, Password, Username
from shared.domain.exceptions import NotFoundError, UnauthorizedError, ValidationError


def _to_output_dto(usuario: Usuario) -> UsuarioOutputDTO:
    """Convierte una entidad de dominio en DTO de salida."""
    return UsuarioOutputDTO(
        id=usuario.id,
        username=usuario.username,
        email=usuario.email,
        first_name=usuario.first_name,
        last_name=usuario.last_name,
        is_active=usuario.is_active,
    )


class RegistrarUsuarioUseCase:
    """Registra un usuario nuevo."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def execute(self, dto: RegistroInputDTO) -> UsuarioOutputDTO:
        """
        Valida, comprueba unicidad y crea el usuario.

        Raises:
            ValidationError: si username/email/password no cumplen reglas,
                             o si username/email ya existen.
        """
        # Value objects: validan formato y normalizan.
        username = Username(dto.username).value
        email = Email(dto.email).value
        password = Password(dto.password).value

        # Unicidad.
        if self._usuario_repo.exists_by_username(username):
            raise ValidationError(
                "Ya existe un usuario con ese username.",
                code="username_taken",
            )
        if self._usuario_repo.exists_by_email(email):
            raise ValidationError(
                "Ya existe un usuario con ese email.",
                code="email_taken",
            )

        # Creamos.
        usuario = self._usuario_repo.create(
            username=username,
            email=email,
            password=password,
            first_name=dto.first_name.strip(),
            last_name=dto.last_name.strip(),
        )

        return _to_output_dto(usuario)


class LoginUseCase:
    """Autentica usuario y devuelve tokens JWT."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def execute(self, dto: LoginInputDTO) -> tuple[UsuarioOutputDTO, TokensOutputDTO]:
        """
        Valida credenciales y emite tokens.

        Raises:
            UnauthorizedError: si las credenciales son incorrectas.
        """
        # authenticate() usa el backend de Django (chequea password + is_active).
        # Es una concesión pragmática: reutilizamos el sistema de auth de Django.
        user = authenticate(username=dto.username, password=dto.password)
        if user is None:
            # Mensaje genérico para no revelar si el username existe.
            raise UnauthorizedError(
                "Credenciales inválidas.",
                code="invalid_credentials",
            )

        if not user.is_active:
            raise UnauthorizedError(
                "La cuenta está desactivada.",
                code="account_inactive",
            )

        # Refrescamos la entidad de dominio.
        usuario_entity = self._usuario_repo.get_by_id(user.id)
        if usuario_entity is None:
            # Caso raro: el usuario existe en auth pero no en nuestro repo.
            raise UnauthorizedError(
                "Credenciales inválidas.",
                code="invalid_credentials",
            )

        # Generamos tokens.
        refresh = RefreshToken.for_user(user)
        tokens = TokensOutputDTO(
            access=str(refresh.access_token),  # type: ignore[attr-defined]
            refresh=str(refresh),
        )

        return _to_output_dto(usuario_entity), tokens


class RefreshTokenUseCase:
    """Renueva el access token a partir de un refresh token."""

    def execute(self, refresh_token: str) -> TokensOutputDTO:
        """..."""
        try:
            refresh = RefreshToken(refresh_token)  # type: ignore[arg-type]
        except Exception as exc:
            raise UnauthorizedError(
                "Refresh token inválido o caducado.",
                code="invalid_refresh_token",
            ) from exc

        with contextlib.suppress(AttributeError):
            refresh.blacklist()

        new_refresh = RefreshToken.for_user(refresh.user)  # type: ignore[attr-defined]
        return TokensOutputDTO(
            access=str(new_refresh.access_token),  # type: ignore[attr-defined]
            refresh=str(new_refresh),
        )


class LogoutUseCase:
    """Invalida el refresh token del usuario (blacklist)."""

    def execute(self, refresh_token: str) -> None:
        """
        Blacklistea el refresh token para que no pueda reutilizarse.

        No lanza excepción si el token ya estaba invalidado (idempotente).
        """
        try:
            token = RefreshToken(refresh_token)  # type: ignore[arg-type]
            token.blacklist()
        except Exception:
            pass


class ObtenerUsuarioActualUseCase:
    """Devuelve el DTO del usuario autenticado."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def execute(self, user_id: object) -> UsuarioOutputDTO:
        """
        Busca el usuario por id.

        Raises:
            NotFoundError: si el usuario no existe.
        """
        usuario = self._usuario_repo.get_by_id(user_id)  # type: ignore[arg-type]
        if usuario is None:
            raise NotFoundError("Usuario no encontrado.", code="user_not_found")
        return _to_output_dto(usuario)


def _hash_token(token: str) -> str:
    """Devuelve el sha256 hex del token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SolicitarResetPasswordUseCase:
    """Genera token de reset y lo guarda hasheado."""

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        token_repo: PasswordResetTokenRepository,
    ) -> None:
        self._usuario_repo = usuario_repo
        self._token_repo = token_repo

    def execute(self, email: str) -> tuple[str, Usuario] | None:
        """
        Si el email existe, genera token y lo devuelve EN CLARO
        (el caller lo envía por email).

        Si el email no existe, devuelve None (no revelamos si existe o no).
        """
        email_norm = Email(email).value
        usuario = self._usuario_repo.get_by_email(email_norm)

        # No revelamos si el email existe (buena práctica de seguridad).
        if usuario is None:
            return None

        # Invalidamos tokens previos vigentes del usuario.
        self._token_repo.invalidate_all_for_user(usuario.id)

        # Generamos token random (URL-safe) y su hash.
        token_plain = secrets.token_urlsafe(48)
        token_hash = _hash_token(token_plain)
        expires_at = timezone.now() + timedelta(hours=24)

        # Persistimos el hash.
        self._token_repo.create(
            user_id=usuario.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return token_plain, usuario


class ConfirmarResetPasswordUseCase:
    """Cambia la contraseña usando un token de reset válido."""

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        token_repo: PasswordResetTokenRepository,
    ) -> None:
        self._usuario_repo = usuario_repo
        self._token_repo = token_repo

    def execute(self, token_plain: str, new_password: str) -> None:
        """
        Valida token, cambia la contraseña y marca el token como usado.

        Raises:
            ValidationError: si el token no existe, ya se usó o expiró,
                             o si la nueva contraseña no cumple las reglas.
        """
        # Validamos la nueva contraseña (VO).
        Password(new_password)

        # Buscamos por hash.
        token_hash = _hash_token(token_plain)
        token_data = self._token_repo.get_by_hash(token_hash)

        if token_data is None:
            raise ValidationError(
                "Token de recuperación inválido.",
                code="reset_token_invalid",
            )

        if token_data.used_at is not None:
            raise ValidationError(
                "Este token ya fue utilizado.",
                code="reset_token_used",
            )

        if not token_data.is_usable:
            raise ValidationError(
                "El token ha caducado.",
                code="reset_token_expired",
            )

        # Cambiamos la contraseña y marcamos el token como usado.
        self._usuario_repo.set_password(token_data.user_id, new_password)
        self._token_repo.mark_as_used(token_hash)
