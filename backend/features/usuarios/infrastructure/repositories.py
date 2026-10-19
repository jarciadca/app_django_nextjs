"""
Implementaciones concretas de los repositorios de `usuarios`.

Usan Django ORM. Traducen entre entidades de dominio y modelos Django.
"""

from datetime import datetime
from uuid import UUID

from features.usuarios.domain.entities import PasswordResetTokenData, Usuario
from features.usuarios.infrastructure.models import PasswordResetToken
from features.usuarios.infrastructure.models import Usuario as UsuarioModel


def _to_entity(model: UsuarioModel) -> Usuario:
    """Convierte un modelo Django `Usuario` en entidad de dominio."""
    return Usuario(
        id=model.id,
        username=model.username,
        email=model.email,
        first_name=model.first_name,
        last_name=model.last_name,
        is_active=model.is_active,
        is_staff=model.is_staff,
        date_joined=model.date_joined,
    )


class DjangoUsuarioRepository:
    """Implementación Django ORM de UsuarioRepository."""

    def get_by_id(self, user_id: UUID) -> Usuario | None:
        """Busca por UUID; devuelve None si no existe."""
        try:
            model = UsuarioModel.objects.get(id=user_id)
        except UsuarioModel.DoesNotExist:
            return None
        return _to_entity(model)

    def get_by_username(self, username: str) -> Usuario | None:
        """Busca por username; case-sensitive."""
        try:
            model = UsuarioModel.objects.get(username=username)
        except UsuarioModel.DoesNotExist:
            return None
        return _to_entity(model)

    def get_by_email(self, email: str) -> Usuario | None:
        """Busca por email; normaliza a minúsculas."""
        try:
            model = UsuarioModel.objects.get(email=email.lower())
        except UsuarioModel.DoesNotExist:
            return None
        return _to_entity(model)

    def exists_by_username(self, username: str) -> bool:
        """True si ya hay un usuario con ese username."""
        return UsuarioModel.objects.filter(username=username).exists()

    def exists_by_email(self, email: str) -> bool:
        """True si ya hay un usuario con ese email."""
        return UsuarioModel.objects.filter(email=email.lower()).exists()

    def create(
        self,
        *,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> Usuario:
        """
        Crea el usuario con `create_user` (hashea la contraseña).
        Devuelve la entidad.
        """
        model = UsuarioModel.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return _to_entity(model)

    def set_password(self, user_id: UUID, new_password: str) -> None:
        """Cambia la contraseña hasheándola."""
        model = UsuarioModel.objects.get(id=user_id)
        model.set_password(new_password)
        model.save(update_fields=["password"])


def _token_to_entity(model: PasswordResetToken) -> PasswordResetTokenData:
    """Convierte un modelo Django PasswordResetToken en entidad de dominio."""
    return PasswordResetTokenData(
        id=model.id,
        user_id=model.user_id,
        token_hash=model.token_hash,
        created_at=model.created_at,
        expires_at=model.expires_at,
        used_at=model.used_at,
    )


class DjangoPasswordResetTokenRepository:
    """Implementación Django ORM de PasswordResetTokenRepository."""

    def create(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        """Inserta un token nuevo."""
        PasswordResetToken.objects.create(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    def get_by_hash(self, token_hash: str) -> PasswordResetTokenData | None:
        """Busca por hash; devuelve None si no existe."""
        try:
            model = PasswordResetToken.objects.get(token_hash=token_hash)
        except PasswordResetToken.DoesNotExist:
            return None
        return _token_to_entity(model)

    def mark_as_used(self, token_hash: str) -> None:
        """Marca como usado el token con ese hash."""
        from django.utils import timezone  # local para no ensuciar el módulo

        PasswordResetToken.objects.filter(token_hash=token_hash).update(
            used_at=timezone.now(),
        )

    def invalidate_all_for_user(self, user_id: UUID) -> None:
        """Marca como usados todos los tokens vigentes del usuario."""
        from django.utils import timezone  # local

        PasswordResetToken.objects.filter(user_id=user_id, used_at__isnull=True).update(
            used_at=timezone.now(),
        )
