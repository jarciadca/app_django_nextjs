"""
Casos de uso del slice `revistas`.

════════════════════════════════════════════════════════════════════
RELACIÓN CON LA API
────────────────────────────────────────────────────────────────────
Cada caso de uso se corresponde con UNA operación REST:

    Endpoint REST                           Use Case
    ─────────────────────────────────────────────────────────────
    GET    /api/revistas/                   ListarRevistasUseCase
    GET    /api/revistas/<uuid>/            ObtenerRevistaUseCase
    POST   /api/revistas/                   CrearRevistaUseCase
    PUT    /api/revistas/<uuid>/            ActualizarRevistaUseCase
    DELETE /api/revistas/<uuid>/            EliminarRevistaUseCase

Los use cases NO conocen HTTP, ni DRF, ni Django ORM. Solo:
  - Reciben un DTO (`RevistaInputDTO`) o parámetros primitivos.
  - Validan reglas de negocio (VOs, unicidad).
  - Llaman al repositorio (interfaz de dominio).
  - Devuelven un DTO (`RevistaOutputDTO`) o lanzan excepción de dominio.

Excepciones de dominio que pueden lanzar y su traducción HTTP (en el
handler global `shared/infrastructure/exception_handler.py`):
  - ValidationError  → 400 Bad Request
  - ConflictError    → 409 Conflict
  - NotFoundError    → 404 Not Found
════════════════════════════════════════════════════════════════════
"""

# `UUID` para tipar el id de los recursos en URLs y repos.
from uuid import UUID

# DTOs de entrada/salida (misma capa `application`).
from features.revistas.application.dtos import (
    RevistaInputDTO,
    RevistaOutputDTO,
)

# Entidad de dominio (la que devuelve el repositorio).
from features.revistas.domain.entities import Revista

# Interfaz del repositorio (puerto).
from features.revistas.domain.repositories import RevistaRepository

# Value Object del ISSN (valida formato + checksum).
from features.revistas.domain.value_objects import ISSN

# Excepciones de dominio compartidas.
# API: el handler global las traduce a respuestas problem+json.
from shared.domain.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)


def _to_dto(revista: Revista) -> RevistaOutputDTO:
    """
    Convierte una entidad de dominio en el DTO de salida.

    API: esta función define la forma pública del JSON de una revista.
    Si mañana quieres exponer más campos, añádelos aquí y en el
    `RevistaOutputSerializer`.

    Args:
        revista: entidad del dominio.

    Returns:
        DTO listo para que el serializer lo convierta a JSON.
    """
    return RevistaOutputDTO(
        id=revista.id,
        nombre=revista.nombre,
        issn=revista.issn,
        editorial=revista.editorial,
        pais=revista.pais,
        sitio_web=revista.sitio_web,
    )


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Listar revistas
# API: GET /api/revistas/?search=&ordering=&page=&page_size=
# ═══════════════════════════════════════════════════════════════════
class ListarRevistasUseCase:
    """
    Lista revistas con búsqueda, orden y paginación.

    API: la vista extrae los query params de `request.query_params` y
    se los pasa a `execute()`. Este use case valida que `page` y
    `page_size` estén en rangos razonables y delega en el repositorio.
    """

    def __init__(self, repo: RevistaRepository) -> None:
        # Inyección de dependencia: el repo se pasa desde la vista.
        # API: en `RevistasListView.get()` se instancia
        # `DjangoRevistaRepository()` y se pasa aquí.
        self._repo = repo

    def execute(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[RevistaOutputDTO], int]:
        """
        Ejecuta el listado.

        Args:
            search: `?search=nature`.
            ordering: `?ordering=-nombre`.
            page: `?page=2` (1-based).
            page_size: `?page_size=20`.

        Returns:
            (lista de DTOs, total sin paginar)

        Raises:
            ValidationError: si `page` o `page_size` están fuera de rango.
                             API: handler global → 400 problem+json.

        Nota API: el total (segundo elemento de la tupla) se convierte
        en el campo `"count"` del JSON paginado.
        """
        # Validaciones de paginación (lógica de negocio: rangos válidos).
        if page < 1:
            raise ValidationError(
                "page debe ser >= 1.",
                code="page_invalid",
            )
        if page_size < 1 or page_size > 100:
            raise ValidationError(
                "page_size debe estar entre 1 y 100.",
                code="page_size_invalid",
            )

        # Cálculo del offset para el slicing del repositorio.
        offset = (page - 1) * page_size

        # Delegamos en el repositorio (que aplica search + ordering + paginación).
        items, total = self._repo.list_all(
            search=search,
            ordering=ordering,
            offset=offset,
            limit=page_size,
        )

        # Convertimos entidades → DTOs de salida.
        return [_to_dto(r) for r in items], total


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Obtener una revista por id
# API: GET /api/revistas/<uuid>/
# ═══════════════════════════════════════════════════════════════════
class ObtenerRevistaUseCase:
    """
    Devuelve una revista por su UUID.

    API: si la revista no existe, lanza NotFoundError → handler global
    responde 404 problem+json con `title: "revista_not_found"`.
    """

    def __init__(self, repo: RevistaRepository) -> None:
        self._repo = repo

    def execute(self, revista_id: UUID) -> RevistaOutputDTO:
        """
        Args:
            revista_id: UUID de la URL.

        Returns:
            DTO de la revista.

        Raises:
            NotFoundError: si no existe.
        """
        revista = self._repo.get_by_id(revista_id)
        if revista is None:
            # API: `NotFoundError` → 404 problem+json.
            raise NotFoundError(
                "Revista no encontrada.",
                code="revista_not_found",
            )
        return _to_dto(revista)


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Crear una revista
# API: POST /api/revistas/
# ═══════════════════════════════════════════════════════════════════
class CrearRevistaUseCase:
    """
    Crea una revista nueva.

    API: es el flujo de `POST /api/revistas/`. Valida formato del ISSN
    (checksum) y unicidad antes de persistir.
    """

    def __init__(self, repo: RevistaRepository) -> None:
        self._repo = repo

    def execute(self, dto: RevistaInputDTO) -> RevistaOutputDTO:
        """
        Args:
            dto: datos del request (ya validados por el serializer de forma).

        Returns:
            DTO de la revista creada (con id asignado).

        Raises:
            ValidationError: si el nombre está vacío o el ISSN es inválido.
                             API: 400 problem+json.
            ConflictError: si ya existe una revista con ese ISSN.
                           API: 409 problem+json.
        """
        # 1) Validar ISSN con el VO (formato + checksum).
        #    API: si falla, ValidationError → 400.
        issn = ISSN(dto.issn).value

        # 2) Validar nombre (mínimo, no vacío).
        #    API: si falla, ValidationError → 400.
        nombre = dto.nombre.strip()
        if not nombre:
            raise ValidationError(
                "El nombre es obligatorio.",
                code="nombre_empty",
            )

        # 3) Unicidad de ISSN (consulta a BD antes de insertar).
        #    API: si ya existe, ConflictError → 409.
        #    ¿Por qué comprobar ANTES en vez de dejar que la BD lo rechace?
        #    Porque el error de la BD sería un IntegrityError genérico
        #    (500 Internal Server Error). Aquí damos un 409 con código
        #    específico, que el frontend puede usar para resaltar el campo.
        if self._repo.exists_by_issn(issn):
            raise ConflictError(
                "Ya existe una revista con ese ISSN.",
                code="issn_taken",
            )

        # 4) Crear en el repositorio (que hace INSERT en PostgreSQL).
        #    Los campos opcionales: normalizamos "" a None para coherencia
        #    en el DTO de salida (JSON devolverá null en vez de "").
        revista = self._repo.create(
            nombre=nombre,
            issn=issn,
            editorial=(dto.editorial or "").strip() or None,
            pais=(dto.pais or "").strip().upper() or None,
            sitio_web=(dto.sitio_web or "").strip() or None,
        )

        # 5) Devolver DTO al serializer.
        return _to_dto(revista)


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Actualizar una revista
# API: PUT /api/revistas/<uuid>/
# ═══════════════════════════════════════════════════════════════════
class ActualizarRevistaUseCase:
    """
    Actualiza una revista existente.

    API: `PUT /api/revistas/<uuid>/`. Comportamiento:
      - Si la revista no existe → NotFoundError (404).
      - Si el nuevo ISSN choca con OTRA revista → ConflictError (409).
      - Si el nuevo ISSN es igual al actual → se permite (no es conflicto).
    """

    def __init__(self, repo: RevistaRepository) -> None:
        self._repo = repo

    def execute(
        self,
        revista_id: UUID,
        dto: RevistaInputDTO,
    ) -> RevistaOutputDTO:
        """
        Args:
            revista_id: UUID de la URL.
            dto: nuevos datos.

        Returns:
            DTO de la revista actualizada.

        Raises:
            ValidationError: nombre vacío o ISSN inválido. → 400.
            NotFoundError: la revista no existe. → 404.
            ConflictError: el ISSN pertenece a OTRA revista. → 409.
        """
        # 1) Validar ISSN (formato + checksum).
        issn = ISSN(dto.issn).value

        # 2) Validar nombre.
        nombre = dto.nombre.strip()
        if not nombre:
            raise ValidationError(
                "El nombre es obligatorio.",
                code="nombre_empty",
            )

        # 3) Unicidad con EXCLUDE_ID.
        #    La clave: excluimos la propia revista del chequeo. Si el
        #    usuario actualiza solo el nombre, el ISSN es "el mismo" que
        #    ya tiene → sin `exclude_id` daríamos un falso 409.
        if self._repo.exists_by_issn(issn, exclude_id=revista_id):
            raise ConflictError(
                "Ya existe otra revista con ese ISSN.",
                code="issn_taken",
            )

        # 4) Update en repositorio.
        revista = self._repo.update(
            revista_id,
            nombre=nombre,
            issn=issn,
            editorial=(dto.editorial or "").strip() or None,
            pais=(dto.pais or "").strip().upper() or None,
            sitio_web=(dto.sitio_web or "").strip() or None,
        )

        # 5) Si `update` devuelve None, la revista no existía.
        #    API: NotFoundError → 404.
        if revista is None:
            raise NotFoundError(
                "Revista no encontrada.",
                code="revista_not_found",
            )

        return _to_dto(revista)


# ═══════════════════════════════════════════════════════════════════
# USE CASE: Eliminar una revista
# API: DELETE /api/revistas/<uuid>/
# ═══════════════════════════════════════════════════════════════════
class EliminarRevistaUseCase:
    """
    Elimina una revista.

    API: `DELETE /api/revistas/<uuid>/`. Devuelve None si tiene éxito
    (la vista responderá 204 No Content). Si no existe → 404.

    Nota futura (Fase 4c): cuando existan artículos con FK a revista,
    borrar una revista que tiene artículos lanzará ProtectedError de
    Django. El handler global lo traducirá a 409 si añadimos ese mapeo
    en Fase 4c. Por ahora no hay dependencias.
    """

    def __init__(self, repo: RevistaRepository) -> None:
        self._repo = repo

    def execute(self, revista_id: UUID) -> None:
        """
        Args:
            revista_id: UUID de la URL.

        Raises:
            NotFoundError: si no existe. → 404.
        """
        if not self._repo.delete(revista_id):
            raise NotFoundError(
                "Revista no encontrada.",
                code="revista_not_found",
            )
