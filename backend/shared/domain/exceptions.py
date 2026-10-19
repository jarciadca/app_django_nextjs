"""
Excepciones de dominio compartidas por todos los features.

Estas excepciones viven en la capa de dominio, sin dependencia de Django ni DRF.
El handler global (shared/infrastructure/exception_handler.py) las traduce
a respuestas HTTP con el formato application/problem+json.
"""


class DomainError(Exception):
    """
    Excepción base de TODAS las excepciones de dominio.

    Cualquier excepción que herede de DomainError es "esperada" y será
    traducida por el handler global. Las excepciones que NO hereden de
    DomainError se consideran bugs (500 Internal Server Error).

    Attributes:
        message: mensaje legible en español para mostrar al usuario.
        code: identificador estable (snake_case) para que el frontend
              pueda reaccionar programáticamente sin parsear el mensaje.
    """

    def __init__(self, message: str, code: str = "domain_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(DomainError):
    """
    La entrada del usuario no cumple las reglas de negocio.

    Ejemplos:
        - username ya en uso.
        - email con formato inválido.
        - contraseña demasiado corta.

    Mapea a HTTP 400 Bad Request.
    """

    def __init__(self, message: str, code: str = "validation_error") -> None:
        super().__init__(message, code)


class NotFoundError(DomainError):
    """
    Un recurso solicitado no existe.

    Ejemplos:
        - Usuario con id X no encontrado.
        - Token de reset no encontrado.

    Mapea a HTTP 404 Not Found.
    """

    def __init__(self, message: str, code: str = "not_found") -> None:
        super().__init__(message, code)


class UnauthorizedError(DomainError):
    """
    El usuario no está autenticado o sus credenciales son inválidas.

    Ejemplos:
        - Username/password incorrectos.
        - Refresh token inválido o caducado.

    Mapea a HTTP 401 Unauthorized.
    """

    def __init__(self, message: str, code: str = "unauthorized") -> None:
        super().__init__(message, code)


class ForbiddenError(DomainError):
    """
    El usuario está autenticado pero no tiene permiso.

    Mapea a HTTP 403 Forbidden.
    """

    def __init__(self, message: str, code: str = "forbidden") -> None:
        super().__init__(message, code)


class ConflictError(DomainError):
    """
    La operación entra en conflicto con el estado actual.

    Ejemplos:
        - Ya existe un usuario con ese username o email.

    Mapea a HTTP 409 Conflict.
    """

    def __init__(self, message: str, code: str = "conflict") -> None:
        super().__init__(message, code)
