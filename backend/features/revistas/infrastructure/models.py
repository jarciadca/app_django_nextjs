"""
Modelos Django del slice `revistas`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Este modelo es la REPRESENTACIÓN EN BASE DE DATOS del recurso REST
`/api/revistas/`. Cada instancia de `Revista` corresponde a un objeto
JSON que el frontend verá:

    {
      "id": "uuid",
      "nombre": "Nature",
      "issn": "0028-0836",
      "editorial": "Springer Nature",
      "pais": "GB",
      "sitio_web": "https://www.nature.com"
    }

El modelo NO se expone directamente en la API: los serializers de DRF
se encargan de traducir modelo → JSON y JSON → modelo. Esta separación
es clave en hexagonal (infrastructure/modelos + infrastructure/serializers).

Las validaciones de negocio (checksum de ISSN) NO están aquí. Viven en
domain/value_objects.py. El modelo solo aplica restricciones de BD
(unique, max_length, null).
════════════════════════════════════════════════════════════════════
"""

# `uuid` para generar identificadores únicos como PK.
# API: el UUID se expone en el JSON como "id" y se usa en URLs
#      como /api/revistas/<uuid>/.
import uuid

# `models` de Django: aquí viven todos los tipos de campo de BD.
# API: cada campo del modelo se traduce a un tipo JSON en el serializer
#      (CharField → string, URLField → string, etc.).
from django.db import models


class Revista(models.Model):
    """
    Revista académica.

    ┌─────────────────────────────────────────────────────────────┐
    │ RECURSO REST: /api/revistas/                                │
    │ OPERACIONES:                                                │
    │   GET    /api/revistas/          → lista (RevistasListView) │
    │   POST   /api/revistas/          → crear                    │
    │   GET    /api/revistas/<uuid>/   → detalle                  │
    │   PUT    /api/revistas/<uuid>/   → actualizar               │
    │   DELETE /api/revistas/<uuid>/   → eliminar                 │
    └─────────────────────────────────────────────────────────────┘

    En Fase 4c, los artículos tendrán una FK a esta tabla:
    `articulo.revista = ForeignKey(Revista)`. Es decir, el recurso
    /api/articulos/ incluirá un campo "revista_id" que apunta aquí.
    """

    # ──────────────────────────────────────────────────────────────
    # PK con UUID (no entero autoincremental)
    # ──────────────────────────────────────────────────────────────
    # API: el UUID se expone en el JSON como "id". Es el identificador
    #      que el frontend usa en las URLs /api/revistas/<uuid>/.
    #      UUID vs entero: no expone el orden de creación (más seguro),
    #      es difícil de enumerar, y encaja con APIs públicas.
    #      `editable=False`: el usuario no puede fijarlo, lo genera Django.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ──────────────────────────────────────────────────────────────
    # CAMPO: nombre
    # ──────────────────────────────────────────────────────────────
    # API: se serializa como `"nombre": "Nature"` (string).
    # `db_index=True`: crea índice en PostgreSQL porque el repo lo usa
    #                  en filtros de búsqueda (`?search=nature`).
    # `max_length=255`: límite a nivel de BD. La validación de forma
    #                   también la hace el serializer (CharField max_length=255).
    nombre = models.CharField(max_length=255, db_index=True)

    # ──────────────────────────────────────────────────────────────
    # CAMPO: issn
    # ──────────────────────────────────────────────────────────────
    # API: se serializa como `"issn": "0028-0836"`.
    # `unique=True`: restricción de BD a nivel único. Si dos revistas
    #               intentan guardar el mismo ISSN, PostgreSQL lanza
    #               IntegrityError (que el handler global convertiría en 500
    #               si no lo validamos antes). Por eso en el caso de uso
    #               `CrearRevistaUseCase` hacemos `exists_by_issn()` ANTES
    #               de crear → devolvemos 409 Conflict limpio.
    # `db_index=True`: el repo hace `filter(issn=...)` en búsquedas,
    #                  conviene que esté indexado.
    # `max_length=9`: 8 caracteres + guion = 9. El VO ISSN lo valida de
    #                 forma estricta (formato + checksum) en domain.
    issn = models.CharField(max_length=9, unique=True, db_index=True)

    # ──────────────────────────────────────────────────────────────
    # CAMPO: editorial
    # ──────────────────────────────────────────────────────────────
    # API: `"editorial": "Springer Nature"` o `null`.
    # `blank=True`: permite string vacío en formularios Django.
    # `null=True`: permite NULL en BD → el JSON devolverá `null`.
    # Los campos opcionales del JSON se declaran así en el modelo.
    editorial = models.CharField(max_length=255, blank=True, null=True)

    # ──────────────────────────────────────────────────────────────
    # CAMPO: pais
    # ──────────────────────────────────────────────────────────────
    # API: `"pais": "GB"` o `null`.
    # `max_length=2`: código ISO de 2 letras (GB, ES, MX).
    # `db_index=True`: útil para `?search=` y futuros filtros por país.
    pais = models.CharField(max_length=2, blank=True, null=True, db_index=True)

    # ──────────────────────────────────────────────────────────────
    # CAMPO: sitio_web
    # ──────────────────────────────────────────────────────────────
    # API: `"sitio_web": "https://www.nature.com"` o `null`.
    # `URLField`: valida formato de URL a nivel de BD/forms (aunque
    #             en la API lo valida el serializer URLField).
    #             El handler global lo traduce a 400 si es inválido.
    sitio_web = models.URLField(blank=True, null=True)

    # ──────────────────────────────────────────────────────────────
    # METADATOS DE AUDITORÍA (no expuestos en la API por defecto)
    # ──────────────────────────────────────────────────────────────
    # `auto_now_add=True`: al crear el registro, guarda la fecha actual.
    # API: si quisiéramos exponer estas fechas, las añadiríamos al
    #      RevistaOutputSerializer. Por ahora no las exponemos.
    created_at = models.DateTimeField(auto_now_add=True)
    # `auto_now=True`: cada `save()` actualiza esta fecha.
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Configuración del modelo.

        `db_table`: nombre explícito de la tabla en PostgreSQL.
                    API: no afecta a la API (los endpoints son /api/revistas/,
                    no el nombre de la tabla). Solo afecta a SQL/migrations.
        `verbose_name`: nombre legible en el panel admin de Django.
        `ordering`: orden por defecto del queryset. API: si el repositorio
                    no aplica `?ordering=`, este es el orden por defecto
                    que verá el frontend.
        """

        db_table = "revistas_revista"
        verbose_name = "revista"
        verbose_name_plural = "revistas"
        ordering = ["nombre"]

    def __str__(self) -> str:
        """
        Representación legible para el admin de Django y logs.

        API: no se usa en la API (el JSON se construye con el serializer),
        pero sí aparece en el admin y en tracebacks de errores.
        """
        return f"{self.nombre} ({self.issn})"
