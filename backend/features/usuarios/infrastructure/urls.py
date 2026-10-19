"""
Rutas URL del slice `usuarios`.
"""

from django.urls import path

from features.usuarios.infrastructure.views import (
    ConfirmarResetPasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    RegistroView,
    SolicitarResetPasswordView,
)

app_name = "usuarios"

urlpatterns = [
    # Autenticación.
    path("registro/", RegistroView.as_view(), name="registro"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    # Recuperación de contraseña.
    path(
        "password-reset/solicitar/",
        SolicitarResetPasswordView.as_view(),
        name="password-reset-solicitar",
    ),
    path(
        "password-reset/confirmar/",
        ConfirmarResetPasswordView.as_view(),
        name="password-reset-confirmar",
    ),
]
