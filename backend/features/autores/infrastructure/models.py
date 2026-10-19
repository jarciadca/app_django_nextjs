"""
Modelos Django del slice `autores`.
"""

import uuid

from django.db import models


def autor_foto_upload_to(instance: "Autor", filename: str) -> str:
    """
    Genera la ruta de la foto de autor.

    Ejemplo: autores/fotos/f5134d90-...-....jpg
    """
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"autores/fotos/{instance.id}.{extension}"


class Autor(models.Model):
    """
    Autor académico.

    Puede estar asociado a uno o varios artículos (relación M2M en Fase 4c).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nombre = models.CharField(max_length=150, db_index=True)
    apellido = models.CharField(max_length=150, db_index=True)
    email = models.EmailField(db_index=True)
    afiliacion = models.CharField(max_length=255, blank=True, default="")

    orcid = models.CharField(
        max_length=19,
        blank=True,
        null=True,
        db_index=True,
        help_text="Formato 0000-0000-0000-000X.",
    )
    pais = models.CharField(max_length=2, blank=True, null=True, db_index=True)
    bio = models.TextField(blank=True, default="")

    foto = models.ImageField(
        upload_to=autor_foto_upload_to,
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "autores_autor"
        verbose_name = "autor"
        verbose_name_plural = "autores"
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=["apellido", "nombre"]),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()
