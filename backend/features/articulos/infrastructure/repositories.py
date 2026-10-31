"""
Implementación Django ORM del repositorio de artículos.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from django.db.models import Q

from features.articulos.domain.entities import Articulo
from features.articulos.infrastructure.models import Articulo as ArticuloModel


def _to_entity(model: ArticuloModel) -> Articulo:
    """Convierte modelo Django → entidad de dominio."""
    return Articulo(
        id=model.id,
        titulo=model.titulo,
        resumen=model.resumen,
        palabras_clave=model.palabras_clave,
        doi=model.doi,
        anio=model.anio,
        idioma=model.idioma,
        estado=model.estado,
        fecha_publicacion=model.fecha_publicacion,
        revista_id=model.revista_id,
    )


class DjangoArticuloRepository:
    """Implementación Django ORM de ArticuloRepository."""

    def list_all(
        self,
        *,
        search: str | None = None,
        estado: str | None = None,
        revista_id: UUID | None = None,
        anio: int | None = None,
        anio_min: int | None = None,
        anio_max: int | None = None,
        idioma: str | None = None,
        ordering: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Articulo], int]:
        qs = ArticuloModel.objects.all()

        # Filtros.
        if search:
            q = search.strip()
            qs = qs.filter(
                Q(titulo__icontains=q) | Q(resumen__icontains=q) | Q(palabras_clave__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        if revista_id:
            qs = qs.filter(revista_id=revista_id)
        if anio is not None:
            qs = qs.filter(anio=anio)
        if anio_min is not None:
            qs = qs.filter(anio__gte=anio_min)
        if anio_max is not None:
            qs = qs.filter(anio__lte=anio_max)
        if idioma:
            qs = qs.filter(idioma=idioma)

        # Ordenamiento con lista blanca.
        allowed = {"titulo", "anio", "fecha_publicacion", "created_at"}
        if ordering and ordering.lstrip("-") in allowed:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-anio", "-fecha_publicacion", "titulo")

        total = qs.count()
        page = qs[offset : offset + limit]
        return [_to_entity(m) for m in page], total

    def get_by_id(self, articulo_id: UUID) -> Articulo | None:
        try:
            model = ArticuloModel.objects.get(id=articulo_id)
        except ArticuloModel.DoesNotExist:
            return None
        return _to_entity(model)

    def exists_by_doi(self, doi: str, exclude_id: UUID | None = None) -> bool:
        qs = ArticuloModel.objects.filter(doi=doi)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return qs.exists()

    def create(
        self,
        *,
        titulo: str,
        resumen: str,
        palabras_clave: str,
        doi: str | None,
        anio: int,
        idioma: str,
        estado: str,
        fecha_publicacion: date | None,
        revista_id: UUID,
    ) -> Articulo:
        model = ArticuloModel.objects.create(
            titulo=titulo,
            resumen=resumen,
            palabras_clave=palabras_clave,
            doi=doi,
            anio=anio,
            idioma=idioma,
            estado=estado,
            fecha_publicacion=fecha_publicacion,
            revista_id=revista_id,
        )
        return _to_entity(model)

    def update(
        self,
        articulo_id: UUID,
        *,
        titulo: str | None = None,
        resumen: str | None = None,
        palabras_clave: str | None = None,
        doi: str | None = None,
        anio: int | None = None,
        idioma: str | None = None,
        estado: str | None = None,
        fecha_publicacion: date | None = None,
        revista_id: UUID | None = None,
    ) -> Articulo | None:
        try:
            model = ArticuloModel.objects.get(id=articulo_id)
        except ArticuloModel.DoesNotExist:
            return None

        if titulo is not None:
            model.titulo = titulo
        if resumen is not None:
            model.resumen = resumen
        if palabras_clave is not None:
            model.palabras_clave = palabras_clave
        if doi is not None:
            model.doi = doi
        if anio is not None:
            model.anio = anio
        if idioma is not None:
            model.idioma = idioma
        if estado is not None:
            model.estado = estado
        if fecha_publicacion is not None:
            model.fecha_publicacion = fecha_publicacion
        if revista_id is not None:
            model.revista_id = revista_id

        model.save()
        return _to_entity(model)

    def delete(self, articulo_id: UUID) -> bool:
        deleted, _ = ArticuloModel.objects.filter(id=articulo_id).delete()
        return deleted > 0
