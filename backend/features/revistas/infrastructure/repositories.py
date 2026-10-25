"""
Implementación Django ORM del repositorio de revistas.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Esta clase es el ÚNICO punto de contacto entre el slice `revistas`
y la base de datos PostgreSQL. Cada método aquí se corresponde con
una operación CRUD expuesta por la API:

    Método del repo   →   Endpoint REST / Acción interna
    ─────────────────────────────────────────────────────────────
    list()            →   GET    /api/revistas/?search=&ordering=&page=
    get_by_id()       →   GET    /api/revistas/<uuid>/
    exists_by_issn()  →   (helper del use case: decide 409 Conflict)
    create()          →   POST   /api/revistas/
    update()          →   PUT    /api/revistas/<uuid>/
    delete()          →   DELETE /api/revistas/<uuid>/

La clase cumple el `Protocol` `RevistaRepository` (definido en domain).
Estructuralmente: cualquier método del Protocol debe existir aquí con
la MISMA firma. mypy valida esta conformidad automáticamente.

Capa hexagonal:
    domain/repositories.py  (interfaz, "puerto")
            ▲
            │ implementa
            │
    infrastructure/repositories.py  (esta clase, "adaptador")
════════════════════════════════════════════════════════════════════
"""

# `UUID` para tipar los IDs (misma firma que el Protocol).
from uuid import UUID

# `Q` de Django permite construir queries OR con `Q(a=x) | Q(b=y)`.
# API: lo usamos para `?search=`: el término se busca en nombre OR issn OR editorial.
from django.db.models import Q

# Importamos la ENTIDAD de dominio (lo que devolvemos/recibimos).
from features.revistas.domain.entities import Revista

# Importamos el MODELO Django (lo que consultamos/escribimos en BD).
# Alias `as RevistaModel` para no confundirlo con la entidad `Revista`.
# API: nunca exponemos `RevistaModel` directamente en el JSON; el repositorio
#      lo convierte a entidad primero, y el serializer convierte la entidad
#      (DTO realmente) a JSON.
from features.revistas.infrastructure.models import Revista as RevistaModel


def _to_entity(model: RevistaModel) -> Revista:
    """
    Convierte un modelo Django `Revista` en la entidad de dominio `Revista`.

    API: esta función se invoca ANTES de devolver el resultado al caso de uso.
    El caso de uso solo maneja entidades, nunca modelos Django. Esto mantiene
    la separación de capas: si mañana cambias a SQLAlchemy, esta función es
    lo único que tocas del repositorio.

    Args:
        model: instancia del modelo Django (`RevistaModel`).

    Returns:
        Entidad inmutable `Revista` del dominio.
    """
    return Revista(
        id=model.id,
        nombre=model.nombre,
        issn=model.issn,
        editorial=model.editorial,
        pais=model.pais,
        sitio_web=model.sitio_web,
    )


class DjangoRevistaRepository:
    """
    Implementación Django ORM de `RevistaRepository`.

    API: esta clase se instancia en cada vista (`RevistasListView`,
    `RevistaDetailView`) para servir los endpoints REST. NO se instancia
    globalmente, se crea nueva por request (es barata: solo envuelve un
    queryset, no mantiene conexión).
    """

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: list
    # API: sirve GET /api/revistas/
    #      Acepta querystring: ?search=, ?ordering=, ?page=, ?page_size=
    # ═══════════════════════════════════════════════════════════════
    def list_all(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Revista], int]:
        """
        Lista revistas con filtros y paginación.

        Args:
            search: término de búsqueda libre (`?search=nature`).
                    Busca en nombre OR issn OR editorial.
            ordering: campo y dirección (`?ordering=-nombre`).
                      Lista blanca para evitar inyección de campos.
            offset: cuántos registros saltar (`(page - 1) * page_size`).
            limit: cuántos devolver (`page_size`).

        Returns:
            (lista de revistas de esta página, TOTAL sin paginar)

        Nota API: el total se devuelve para construir el `"count"` del JSON
        paginado:
            {"count": 142, "page": 1, "page_size": 20, "results": [...]}
        """

        # 1) Queryset base: TODAS las revistas.
        #    Equivale a `SELECT * FROM revistas_revista` (aún sin ejecutar).
        #    Django es lazy: el queryset no toca la BD hasta que lo iteramos.
        qs = RevistaModel.objects.all()

        # 2) Filtro por búsqueda libre (`?search=...`).
        #    API: si el usuario llama `/api/revistas/?search=nature`,
        #    la vista extrae "nature" de query_params y lo pasa aquí.
        if search:
            q = search.strip()
            # `Q(a__icontains=q) | Q(b__icontains=q) | ...` es un OR.
            # `__icontains` = contiene, case-insensitive.
            # SQL generado: WHERE nombre ILIKE '%nature%' OR issn ILIKE ...
            qs = qs.filter(
                Q(nombre__icontains=q) | Q(issn__icontains=q) | Q(editorial__icontains=q)
            )

        # 3) Ordenamiento (`?ordering=...`).
        # API: el frontend puede enviar `?ordering=nombre` o `?ordering=-issn`.
        # SEGURIDAD: solo permitimos estos campos para evitar inyección
        #           de nombres de columna (Django, al hacer `.order_by(user_input)`,
        #           podría fallar con columnas inexistentes o abrir vectores de ataque).
        allowed_ordering = {"nombre", "issn", "editorial", "pais", "created_at"}
        # Orden por defecto: nombre ascendente.
        # Si `?ordering=` viene en la querystring y el campo está permitido,
        # lo aplicamos (respetando el `-` para descendente).
        # Si el campo NO está en la lista blanca, caemos al default por seguridad
        # (evita inyección de nombres de columna).
        if ordering and ordering.lstrip("-") in allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("nombre")

        # 4) Conteo total (antes de paginar).
        # API: este número va al campo "count" del JSON paginado.
        # SQL: SELECT COUNT(*) FROM ...
        total = qs.count()

        # 5) Paginación con slicing.
        # `qs[offset:offset+limit]` → SQL LIMIT ... OFFSET ...
        # Django evalúa la query AQUÍ (primera vez que se itera).
        page = qs[offset : offset + limit]

        # 6) Convertimos cada modelo a entidad de dominio.
        # API: solo se devuelven entidades; la vista las pasará al serializer.
        return [_to_entity(m) for m in page], total

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: get_by_id
    # API: sirve GET /api/revistas/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def get_by_id(self, revista_id: UUID) -> Revista | None:
        """
        Busca una revista por UUID.

        API: usado por `GET /api/revistas/<uuid>/`.
        Si devuelve None, el use case lanza NotFoundError → handler global
        lo traduce a 404 problem+json.

        Args:
            revista_id: UUID del recurso.

        Returns:
            La entidad, o None si no existe.
        """
        try:
            # `objects.get(id=...)` lanza DoesNotExist si no encuentra.
            model = RevistaModel.objects.get(id=revista_id)
        except RevistaModel.DoesNotExist:
            # No es un error: el recurso simplemente no existe.
            # El use case decide qué hacer (lanzar NotFoundError).
            return None
        return _to_entity(model)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: exists_by_issn
    # API: NO es un endpoint. Es un HELPER para decidir 409 Conflict.
    #      Lo invoca `CrearRevistaUseCase` / `ActualizarRevistaUseCase`
    #      ANTES de insertar, para devolver un 409 limpio en vez de un
    #      IntegrityError feo de PostgreSQL (que sería 500).
    # ═══════════════════════════════════════════════════════════════
    def exists_by_issn(self, issn: str, exclude_id: UUID | None = None) -> bool:
        """
        Comprueba si ya existe una revista con ese ISSN.

        API: si `True`, el use case lanza ConflictError → 409 problem+json.
        SQL: SELECT 1 FROM revistas_revista WHERE issn = '...' LIMIT 1

        Args:
            issn: ISSN ya validado (formato + checksum).
            exclude_id: al ACTUALIZAR, excluye esa misma revista del conteo.
                        Sin esto, actualizar el nombre (sin cambiar ISSN)
                        daría "ISSN ya existe" falsamente.

        Returns:
            True si existe (otra revista con ese ISSN).
        """
        qs = RevistaModel.objects.filter(issn=issn)
        if exclude_id is not None:
            # `.exclude(id=...)` añade `AND id != '<exclude_id>'` al WHERE.
            qs = qs.exclude(id=exclude_id)
        # `.exists()` → SELECT EXISTS(...) LIMIT 1. Más rápido que count() > 0.
        return qs.exists()

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: create
    # API: sirve POST /api/revistas/
    # ═══════════════════════════════════════════════════════════════
    def create(
        self,
        *,
        nombre: str,
        issn: str,
        editorial: str | None,
        pais: str | None,
        sitio_web: str | None,
    ) -> Revista:
        """
        Crea una revista y devuelve la entidad resultante.

        API: invocado por `POST /api/revistas/`.
        Los datos llegan ya validados (el serializer validó forma, el use case
        validó negocio: ISSN con checksum, unicidad, etc.).

        Args:
            nombre: nombre de la revista.
            issn: ISSN validado (formato XXXX-XXXX + checksum).
            editorial, pais, sitio_web: campos opcionales (pueden ser None).

        Returns:
            La entidad con el id UUID ya asignado por Django.
        """
        model = RevistaModel.objects.create(
            nombre=nombre,
            issn=issn,
            editorial=editorial,
            pais=pais,
            sitio_web=sitio_web,
        )
        return _to_entity(model)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: update
    # API: sirve PUT /api/revistas/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def update(
        self,
        revista_id: UUID,
        *,
        nombre: str | None = None,
        issn: str | None = None,
        editorial: str | None = None,
        pais: str | None = None,
        sitio_web: str | None = None,
    ) -> Revista | None:
        """
        Actualiza una revista. Solo los campos NO-None se modifican.

        API: invocado por `PUT /api/revistas/<uuid>/`.
        Convención: aunque el endpoint sea PUT (que semánticamente reemplaza
        el recurso entero), tratamos cada campo como opcional para permitir
        actualizaciones parciales. Si `nombre=None`, no se toca.

        Args:
            revista_id: UUID del recurso a actualizar.
            nombre, issn, ...: nuevos valores (o None para mantener el actual).

        Returns:
            La entidad actualizada, o None si el recurso no existía.
            (El use case decide si None implica NotFoundError.)
        """
        try:
            model = RevistaModel.objects.get(id=revista_id)
        except RevistaModel.DoesNotExist:
            return None

        # Actualizamos solo los campos que llegan explícitamente.
        # Patrón `if x is not None` (no `if x:`) para permitir string vacío
        # o None explícitos si el cliente los envía.
        if nombre is not None:
            model.nombre = nombre
        if issn is not None:
            model.issn = issn
        if editorial is not None:
            model.editorial = editorial
        if pais is not None:
            model.pais = pais
        if sitio_web is not None:
            model.sitio_web = sitio_web

        # `save()` hace UPDATE ... WHERE id = ...
        model.save()
        return _to_entity(model)

    # ═══════════════════════════════════════════════════════════════
    # MÉTODO: delete
    # API: sirve DELETE /api/revistas/<uuid>/
    # ═══════════════════════════════════════════════════════════════
    def delete(self, revista_id: UUID) -> bool:
        """
        Elimina una revista.

        API: invocado por `DELETE /api/revistas/<uuid>/`.
        Si devuelve False, el use case lanza NotFoundError → 404.
        Si devuelve True, la vista responde 204 No Content.

        Args:
            revista_id: UUID a borrar.

        Returns:
            True si existía y se borró, False si no existía.
        """
        # `.filter().delete()` devuelve (num_borrados, dict_de_detalles).
        # Ignoramos los detalles con `_`.
        # `filter` (no `get`) → no lanza DoesNotExist si no existe, devuelve (0, {}).
        deleted, _ = RevistaModel.objects.filter(id=revista_id).delete()
        return deleted > 0
