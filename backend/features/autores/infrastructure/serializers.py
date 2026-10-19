"""
Serializers DRF del slice `autores`.
"""

from rest_framework import serializers


class AutorInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Body de POST/PUT de autor."""

    nombre = serializers.CharField(max_length=150)
    apellido = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    afiliacion = serializers.CharField(max_length=255, required=False, default="")
    orcid = serializers.CharField(max_length=19, required=False, allow_null=True, allow_blank=True)
    pais = serializers.CharField(max_length=2, required=False, allow_null=True, allow_blank=True)
    bio = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    foto = serializers.ImageField(required=False, allow_null=True)


class AutorOutputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Salida pública de un autor."""

    id = serializers.UUIDField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    email = serializers.EmailField()
    afiliacion = serializers.CharField()
    orcid = serializers.CharField(allow_null=True)
    pais = serializers.CharField(allow_null=True)
    bio = serializers.CharField(allow_null=True)
    foto = serializers.CharField(allow_null=True)
