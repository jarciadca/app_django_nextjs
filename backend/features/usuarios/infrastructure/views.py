"""
Vistas (adaptadores HTTP) del slice `usuarios`.

Cada vista:
  1. Valida el body con un Serializer.
  2. Construye el DTO de entrada.
  3. Instancia el use case con sus repositorios.
  4. Ejecuta el use case.
  5. Serializa la salida y devuelve la Response.

No contienen lógica de negocio.
"""

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from features.usuarios.application.dtos import (
    ConfirmarResetInputDTO,
    LoginInputDTO,
    RegistroInputDTO,
    SolicitarResetInputDTO,
)
from features.usuarios.application.use_cases import (
    ConfirmarResetPasswordUseCase,
    LoginUseCase,
    LogoutUseCase,
    ObtenerUsuarioActualUseCase,
    RefreshTokenUseCase,
    RegistrarUsuarioUseCase,
    SolicitarResetPasswordUseCase,
)
from features.usuarios.infrastructure.repositories import (
    DjangoPasswordResetTokenRepository,
    DjangoUsuarioRepository,
)
from features.usuarios.infrastructure.serializers import (
    ConfirmarResetInputSerializer,
    LoginInputSerializer,
    RegistroInputSerializer,
    SolicitarResetInputSerializer,
    UsuarioOutputSerializer,
)

# --- Helpers para cookies ---


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Setea la cookie httpOnly con el refresh token."""
    response.set_cookie(
        key=settings.SIMPLE_JWT["AUTH_COOKIE"],
        value=refresh_token,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
        httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
        samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"],
        secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Borra la cookie del refresh token."""
    response.delete_cookie(
        key=settings.SIMPLE_JWT["AUTH_COOKIE"],
        path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
    )


# --- Vistas ---


class RegistroView(APIView):
    """POST /api/auth/registro/ → crea un usuario nuevo."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Valida y ejecuta RegistrarUsuarioUseCase."""
        serializer = RegistroInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = RegistroInputDTO(**serializer.validated_data)
        repo = DjangoUsuarioRepository()
        use_case = RegistrarUsuarioUseCase(repo)
        output = use_case.execute(dto)

        return Response(UsuarioOutputSerializer(output).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/ → devuelve access y setea cookie refresh."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Valida credenciales, emite tokens, setea cookie."""
        serializer = LoginInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = LoginInputDTO(**serializer.validated_data)
        repo = DjangoUsuarioRepository()
        use_case = LoginUseCase(repo)
        usuario_dto, tokens_dto = use_case.execute(dto)

        # Preparamos la respuesta con el access en el body.
        response = Response(
            {
                "access": tokens_dto.access,
                "usuario": UsuarioOutputSerializer(usuario_dto).data,
            },
            status=status.HTTP_200_OK,
        )
        # Refresh token va en cookie httpOnly (no en el body).
        _set_refresh_cookie(response, tokens_dto.refresh)
        return response


class RefreshView(APIView):
    """POST /api/auth/refresh/ → renueva el access leyendo la cookie."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Lee cookie, valida refresh, emite nuevo par y rota cookie."""
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"])
        if not refresh_token:
            return Response(
                {
                    "type": "https://docs.app_django_nextjs.local/errors/missing_refresh_token",
                    "title": "missing_refresh_token",
                    "status": 401,
                    "detail": "No se encontró el refresh token en la cookie.",
                    "instance": request.path,
                },
                status=status.HTTP_401_UNAUTHORIZED,
                content_type="application/problem+json",
            )

        use_case = RefreshTokenUseCase()
        tokens_dto = use_case.execute(refresh_token)

        response = Response({"access": tokens_dto.access}, status=status.HTTP_200_OK)
        _set_refresh_cookie(response, tokens_dto.refresh)
        return response


class LogoutView(APIView):
    """POST /api/auth/logout/ → invalida refresh y borra cookie."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Blacklistea el refresh (idempotente) y borra la cookie."""
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"])
        if refresh_token:
            LogoutUseCase().execute(refresh_token)

        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_refresh_cookie(response)
        return response


class MeView(APIView):
    """GET /api/auth/me/ → datos del usuario autenticado."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Devuelve el usuario del access token."""
        repo = DjangoUsuarioRepository()
        use_case = ObtenerUsuarioActualUseCase(repo)
        output = use_case.execute(request.user.id)
        return Response(UsuarioOutputSerializer(output).data)


class SolicitarResetPasswordView(APIView):
    """POST /api/auth/password-reset/solicitar/ → envía email con enlace."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Genera token y envía email (si el email existe)."""
        serializer = SolicitarResetInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = SolicitarResetInputDTO(email=serializer.validated_data["email"])
        usuario_repo = DjangoUsuarioRepository()
        token_repo = DjangoPasswordResetTokenRepository()
        use_case = SolicitarResetPasswordUseCase(usuario_repo, token_repo)
        result = use_case.execute(dto.email)

        # Si el email existe, enviamos el email.
        if result is not None:
            token_plain, usuario = result
            # En local, esto se imprime en consola (EMAIL_BACKEND=console).
            reset_url = f"http://localhost:3000/reset-password?token={token_plain}"
            send_mail(
                subject="Recuperación de contraseña",
                message=(
                    f"Hola {usuario.username},\n\n"
                    f"Para restablecer tu contraseña, haz clic en:\n{reset_url}\n\n"
                    f"El enlace caduca en 24 horas. Si no solicitaste esto, ignora el mensaje."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                fail_silently=False,
            )

        # Respuesta genérica SIEMPRE (no revelamos si el email existe).
        return Response(
            {"detail": "Si el email existe, recibirás instrucciones en breve."},
            status=status.HTTP_200_OK,
        )


class ConfirmarResetPasswordView(APIView):
    """POST /api/auth/password-reset/confirmar/ → cambia la contraseña."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Valida token y cambia contraseña."""
        serializer = ConfirmarResetInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = ConfirmarResetInputDTO(**serializer.validated_data)
        usuario_repo = DjangoUsuarioRepository()
        token_repo = DjangoPasswordResetTokenRepository()
        use_case = ConfirmarResetPasswordUseCase(usuario_repo, token_repo)
        use_case.execute(dto.token, dto.new_password)

        return Response(
            {"detail": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )
