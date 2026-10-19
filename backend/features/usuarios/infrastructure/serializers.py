"""
Serializers DRF del slice `usuarios`.

Su única responsabilidad es validar ESTRUCTURA (tipos, formatos) y
traducir entre JSON y DTOs. La lógica de negocio vive en los use cases.
"""

from rest_framework import serializers


class RegistroInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Valida el body de POST /api/auth/registro/."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")


class LoginInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Valida el body de POST /api/auth/login/."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class UsuarioOutputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializa un UsuarioOutputDTO a JSON público."""

    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_active = serializers.BooleanField()


class TokensOutputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializa tokens (el refresh NO se expone en el body; va en cookie)."""

    access = serializers.CharField()


class SolicitarResetInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Valida el body de POST /api/auth/password-reset/solicitar/."""

    email = serializers.EmailField()


class ConfirmarResetInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Valida el body de POST /api/auth/password-reset/confirmar/."""

    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, write_only=True)
