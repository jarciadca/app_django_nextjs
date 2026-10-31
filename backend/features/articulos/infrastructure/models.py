"""
Modelos Django del slice `articulos` (Fase 4c.1).

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
En esta subfase SOLO creamos la tabla `Articulo` con sus metadatos
básicos y FK a Revista. NO incluimos todavía:
  - M2M con Autor (va en Fase 4c.2).
  - M2M con Categoria (va en Fase 4c.3).
  - PDF (va en Fase 4c.3).

El modelo se expone en `/api/articulos/` como un recurso REST con
los metadatos básicos.

NOTA IMPORTANTE:
    El modelo Articulo que crearás ahora ya tiene los campos `autores`
    y `categorias` definidos como M2M `through`, pero las tablas
    intermedias NO existen aún (las añadiremos en fases posteriores).
    Es una decisión de diseño: definir los campos en el modelo desde
    el principio evita migraciones múltiples sobre la misma tabla.
    Sin embargo, en esta subfase, las tablas `articulos_articulo_autor`
    y `articulos_articulo_categoria` NO estarán creadas en BD hasta
    Fase 4c.2 y 4c.3 respectivamente.

    ⚠️ Decisión pragmática: para no complicar migraciones, en 4c.1
    vamos a definir el modelo SIN las relaciones M2M. Las añadiremos
    en 4c.2 y 4c.3 con migraciones nuevas. Esto sigue el principio
    de "un cambio, una migración", y facilita hacer rollback si algo
    falla.
════════════════════════════════════════════════════════════════════
"""

import uuid

from django.db import models


class EstadoArticulo(models.TextChoices):
    """
    Estados del ciclo de vida de un artículo.

    API: expuesto como string. Ej: `"estado": "borrador"`.
    """

    BORRADOR = "borrador", "Borrador"
    PUBLICADO = "publicado", "Publicado"


def articulo_pdf_upload_to(instance: "Articulo", filename: str) -> str:
    """
    Ruta de subida del PDF. En 4c.1 el campo `pdf` no existe todavía,
    pero dejamos la función preparada para Fase 4c.3.
    """
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"articulos/pdfs/{instance.id}.{extension}"


class Articulo(models.Model):
    """
    Artículo académico.

    En Fase 4c.1 incluye:
      - Metadatos básicos: título, resumen, palabras clave, DOI, año,
        idioma, estado, fecha de publicación.
      - FK a Revista (obligatoria, PROTECT).

    Se añadirán en fases posteriores:
      - M2M con Autor (Fase 4c.2).
      - M2M con Categoria (Fase 4c.3).
      - PDF (Fase 4c.3).
    """

    # ─── PK UUID ───
    # API: expuesto como "id", usado en /api/articulos/<uuid>/.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ─── Metadatos básicos ───
    # API: título del artículo. Obligatorio, max 500 chars.
    titulo = models.CharField(max_length=500, db_index=True)

    # API: resumen. Puede estar vacío en borrador.
    resumen = models.TextField(blank=True, default="")

    # API: palabras clave separadas por coma. Texto libre.
    palabras_clave = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Separadas por comas. Ej: 'quantum, graphene, entanglement'",
    )

    # ─── DOI (opcional, único si existe) ───
    # API: si existe, no puede repetirse en BD.
    # `null=True` para permitir artículos sin DOI.
    # `unique=True` porque un DOI identifica unívocamente una publicación.
    doi = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text="Digital Object Identifier. Ej: 10.1038/nature12345",
    )

    # ─── Publicación ───
    # API: año de publicación, entre 1900 y 2100.
    anio = models.PositiveSmallIntegerField(
        db_index=True,
        help_text="Año de publicación (1900-2100).",
    )

    # API: código ISO 639-1 (2 letras minúsculas).
    idioma = models.CharField(
        max_length=2,
        default="es",
        help_text="Código ISO 639-1: es, en, fr, de, pt...",
    )

    # API: "borrador" o "publicado".
    estado = models.CharField(
        max_length=20,
        choices=EstadoArticulo.choices,
        default=EstadoArticulo.BORRADOR,
        db_index=True,
    )

    # API: fecha de publicación (opcional en borrador).
    fecha_publicacion = models.DateField(
        null=True,
        blank=True,
        help_text="Obligatoria al publicar (Fase 4c.3).",
    )

    # ─── FK a Revista ───
    # API: `revista_id` en el JSON. `PROTECT`: no se puede borrar una
    # revista que tiene artículos.
    # `related_name="articulos"`: desde Python, `revista.articulos.all()`.
    revista = models.ForeignKey(
        "revistas.Revista",
        on_delete=models.PROTECT,
        related_name="articulos",
        help_text="Revista donde se publicó el artículo.",
    )

    # ─── Auditoría ───
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "articulos_articulo"
        verbose_name = "artículo"
        verbose_name_plural = "artículos"
        # API: orden por defecto en listados (más recientes primero).
        ordering = ["-anio", "-fecha_publicacion", "titulo"]
        indexes = [
            models.Index(fields=["estado", "-anio"]),
            models.Index(fields=["revista", "-anio"]),
        ]

    def __str__(self) -> str:
        """Representación legible: 'Título (año)'."""
        return f"{self.titulo} ({self.anio})"

    @property
    def esta_publicado(self) -> bool:
        """True si el artículo está publicado."""
        return self.estado == EstadoArticulo.PUBLICADO
