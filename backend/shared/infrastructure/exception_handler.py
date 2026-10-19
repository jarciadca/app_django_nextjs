"""
Handler global de excepciones para DRF.

DRF permite registrar un "exception handler" que se invoca cada vez que
una vista lanza una excepción. Aquí lo usamos para:

  1. Traducir excepciones de dominio (DomainError y subclases) a respuestas
     HTTP con el formato application/problem+json (RFC 7807).
  2. Dejar pasar las excepciones que DRF ya sabe manejar (ValidationError,
     AuthenticationFailed, etc.) tal cual, para no reinventar la rueda.
  3. Registrar en logs los errores inesperados (bugs) con traceback completo.

Formato de respuesta (RFC 7807 simplificado):
{
  "type":     "https://docs.example.com/errors/validation_error",
  "title":    "validation_error",
  "status":   400,
  "detail":   "El username ya está en uso.",
  "instance": "/api/auth/registro/"
}
"""

import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

from shared.domain.exceptions import (
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

# Logger dedicado a errores de API. Se configura en LOGGING (settings).
logger = logging.getLogger("api.errors")


# Mapeo de excepción de dominio -> código HTTP.
_DOMAIN_TO_HTTP: dict[type[DomainError], int] = {
    ValidationError: status.HTTP_400_BAD_REQUEST,
    UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
}


def _build_problem_response(
    *,
    exc: DomainError,
    http_status: int,
    instance: str,
) -> Response:
    """Construye la respuesta con formato problem+json."""
    # URL base de documentación de errores; en Fase 7 se puede parametrizar.
    type_uri = f"https://docs.app_django_nextjs.local/errors/{exc.code}"
    body: dict[str, Any] = {
        "type": type_uri,
        "title": exc.code,
        "status": http_status,
        "detail": exc.message,
        "instance": instance,
    }
    # `content_type` especial que indica que es un "problem detail".
    return Response(body, status=http_status, content_type="application/problem+json")


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Punto de entrada del handler.

    Se registra en REST_FRAMEWORK["EXCEPTION_HANDLER"] en settings.

    Args:
        exc: excepción lanzada por la vista o por DRF.
        context: diccionario con "view", "request", "args", "kwargs".

    Returns:
        Response si sabemos cómo manejarla, o None para que Django
        devuelva un 500 estándar (solo pasa con bugs reales).
    """
    # Extraemos la ruta de la request para el campo "instance".
    request = context.get("request")
    instance = request.path if request is not None else ""

    # --- 1) Excepciones de dominio (nuestras) ---
    if isinstance(exc, DomainError):
        # Determinamos el código HTTP según la subclase.
        http_status = _DOMAIN_TO_HTTP.get(type(exc), status.HTTP_400_BAD_REQUEST)
        # Log informativo (no es un bug, es un error esperado).
        logger.info(
            "domain_error",
            extra={"code": exc.code, "status": http_status, "path": instance},
        )
        return _build_problem_response(exc=exc, http_status=http_status, instance=instance)

    # --- 2) Excepciones que DRF ya maneja (ValidationError, NotAuthenticated, etc.) ---
    response = drf_default_handler(exc, context)
    if response is not None:
        return response

    # --- 3) Cualquier otra cosa es un bug: log con traceback y dejamos que Django responda 500 ---
    logger.exception(
        "unhandled_exception",
        extra={"path": instance, "type": type(exc).__name__},
    )
    return None
