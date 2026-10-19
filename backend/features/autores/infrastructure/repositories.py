"""
Implementación Django ORM del repositorio de autores.
"""

from uuid import UUID

from features.autores.domain.entities import Autor
from features.autores.infrastructure.models import Autor as AutorModel


def _to_entity(model: AutorModel) -> Autor:
    """Convierte un modelo Django `Autor` en entidad de dominio."""
    return Autor(
        id=model.id,
        nombre=model.nombre,
        apellido=model.apellido,
        email=model.email,
        afiliacion=model.afiliacion,
        orcid=model.orcid,
        pais=model.pais,
        bio=model.bio,
        foto=model.foto.name if model.foto else None,
    )


class DjangoAutorRepository:
    """Implementación Django ORM de AutorRepository."""

    def list(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Autor], int]:
        """Lista autores con búsqueda, orden y paginación."""
        qs = AutorModel.objects.all()

        # Búsqueda simple en nombre, apellido, email, afiliación.
        if search:
            from django.db.models import Q

            q = search.strip()
            qs = qs.filter(
                Q(nombre__icontains=q)
                | Q(apellido__icontains=q)
                | Q(email__icontains=q)
                | Q(afiliacion__icontains=q)
            )

        # Ordenamiento (lista blanca para evitar inyección de campos).
        allowed_order = {"nombre", "apellido", "email", "created_at"}
        if ordering:
            field = ordering.lstrip("-")
            if field in allowed_order:
                qs = qs.order_by(ordering)
            else:
                qs = qs.order_by("apellido", "nombre")
        else:
            qs = qs.order_by("apellido", "nombre")

        total = qs.count()
        page = qs[offset : offset + limit]
        return [_to_entity(m) for m in page], total

    def get_by_id(self, autor_id: UUID) -> Autor | None:
        try:
            model = AutorModel.objects.get(id=autor_id)
        except AutorModel.DoesNotExist:
            return None
        return _to_entity(model)

    def create(
        self,
        *,
        nombre: str,
        apellido: str,
        email: str,
        afiliacion: str,
        orcid: str | None,
        pais: str | None,
        bio: str | None,
        foto: str | None,
    ) -> Autor:
        model = AutorModel.objects.create(
            nombre=nombre,
            apellido=apellido,
            email=email,
            afiliacion=afiliacion,
            orcid=orcid,
            pais=pais,
            bio=bio or "",
            foto=foto,
        )
        return _to_entity(model)

    def update(
        self,
        autor_id: UUID,
        *,
        nombre: str | None = None,
        apellido: str | None = None,
        email: str | None = None,
        afiliacion: str | None = None,
        orcid: str | None = None,
        pais: str | None = None,
        bio: str | None = None,
        foto: str | None = None,
    ) -> Autor | None:
        try:
            model = AutorModel.objects.get(id=autor_id)
        except AutorModel.DoesNotExist:
            return None

        if nombre is not None:
            model.nombre = nombre
        if apellido is not None:
            model.apellido = apellido
        if email is not None:
            model.email = email
        if afiliacion is not None:
            model.afiliacion = afiliacion
        if orcid is not None:
            model.orcid = orcid
        if pais is not None:
            model.pais = pais
        if bio is not None:
            model.bio = bio
        if foto is not None:
            model.foto = foto

        model.save()
        return _to_entity(model)

    def delete(self, autor_id: UUID) -> bool:
        deleted, _ = AutorModel.objects.filter(id=autor_id).delete()
        return deleted > 0
