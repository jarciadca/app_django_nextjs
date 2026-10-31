"""Serializers DRF del slice `articulos`."""

from rest_framework import serializers


class ArticuloInputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Valida el body de POST/PUT de un artículo."""

    titulo = serializers.CharField(max_length=500)
    anio = serializers.IntegerField()
    revista_id = serializers.UUIDField()
    resumen = serializers.CharField(required=False, allow_blank=True, default="")
    palabras_clave = serializers.CharField(required=False, allow_blank=True, default="")
    doi = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    idioma = serializers.CharField(required=False, default="es")
    estado = serializers.ChoiceField(
        choices=["borrador", "publicado"],
        required=False,
        default="borrador",
    )
    fecha_publicacion = serializers.DateField(required=False, allow_null=True)


class ArticuloOutputSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Salida pública de un artículo."""

    id = serializers.UUIDField()
    titulo = serializers.CharField()
    resumen = serializers.CharField()
    palabras_clave = serializers.CharField()
    doi = serializers.CharField(allow_null=True)
    anio = serializers.IntegerField()
    idioma = serializers.CharField()
    estado = serializers.CharField()
    fecha_publicacion = serializers.DateField(allow_null=True)
    revista_id = serializers.UUIDField()
