"""
Settings comunes a TODOS los entornos.
local.py, production.py y test.py heredan de aquí con `from .base import *`.
"""

# `Path` de pathlib para manipular rutas de forma portable.
from pathlib import Path

# `environ` de django-environ para leer variables tipadas desde .env.
import environ

# ============================================================
# RUTAS BASE
# ============================================================

# BASE_DIR = backend/. Este archivo está en backend/config/settings/base.py.
# parent = settings/, parent.parent = config/, parent.parent.parent = backend/.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ROOT_DIR = raíz del monorepo (un nivel por encima de backend/).
ROOT_DIR = BASE_DIR.parent


# ============================================================
# VARIABLES DE ENTORNO
# ============================================================

# `Env()` crea el lector de variables con tipos y defaults.
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)

# Carga el .env de la raíz del monorepo. Si no existe, no falla.
environ.Env.read_env(ROOT_DIR / ".env")


# ============================================================
# SEGURIDAD
# ============================================================

# Clave para firmar sesiones, tokens, CSRF. NUNCA en el repo.
SECRET_KEY = env("DJANGO_SECRET_KEY")

# Modo debug. En producción debe ser False.
DEBUG = env("DJANGO_DEBUG")

# Hosts permitidos.
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")


# ============================================================
# APLICACIONES INSTALADAS
# ============================================================

INSTALLED_APPS = [
    # Apps internas de Django.
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros.
    "rest_framework",  # DRF: APIs REST.
    "corsheaders",  # CORS para el frontend.
    # Apps propias: se añadirán por feature en fases siguientes.
    "features.usuarios.infrastructure.apps.UsuariosConfig",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    # CORS debe ir primero para interceptar todas las respuestas.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URLS Y WSGI
# ============================================================

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================================================
# BASE DE DATOS
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        # Reutiliza conexiones 60s para no abrir una por request.
        "CONN_MAX_AGE": 60,
    }
}


# ============================================================
# VALIDADORES DE CONTRASEÑA
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ============================================================
# INTERNACIONALIZACIÓN
# ============================================================

LANGUAGE_CODE = "es-es"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ============================================================
# ESTÁTICOS Y MEDIA
# ============================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# PK POR DEFECTO
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# DJANGO REST FRAMEWORK
# ============================================================

REST_FRAMEWORK = {
    # Autenticación JWT (se afina en Fase 3).
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Por defecto exigimos autenticación. Los endpoints públicos lo sobreescriben.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Paginación estándar.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Filtros por querystring.
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}


# ============================================================
# CORS
# ============================================================

# En base vacío; local.py añade localhost:3000.
CORS_ALLOWED_ORIGINS: list[str] = []

# Permite que el frontend envíe cookies (para refresh token httpOnly).
CORS_ALLOW_CREDENTIALS = True


# ============================================================
# MODELO DE USUARIO PERSONALIZADO
# ============================================================

# Django exige que, si usas un User model propio, lo declares ANTES de la primera migración.
# Cambiarlo después es muy doloroso. Lo hacemos aquí desde el primer día.
AUTH_USER_MODEL = "usuarios.Usuario"


# ============================================================
# DJANGO REST FRAMEWORK — EXCEPTION HANDLER
# ============================================================

# Sustituimos el handler por defecto de DRF por el nuestro, que traduce
# DomainError a problem+json y loggea bugs con traceback.
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "shared.infrastructure.exception_handler.custom_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}


# ============================================================
# SIMPLE JWT — CONFIGURACIÓN
# ============================================================

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    # Access token: vida corta (15 min) porque va en memoria del frontend.
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    # Refresh token: vida larga (7 días) porque va en cookie httpOnly.
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Rotación: cada refresh emite un nuevo refresh token (más seguro).
    "ROTATE_REFRESH_TOKENS": True,
    # Al rotar, invalidamos el refresh anterior (requiere app token_blacklist).
    "BLACKLIST_AFTER_ROTATION": True,
    # Algoritmo de firma.
    "ALGORITHM": "HS256",
    # Firma con SECRET_KEY del proyecto.
    "SIGNING_KEY": SECRET_KEY,
    # Nombre del header que llevará el access token.
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Claims del token (podemos añadir datos extra del usuario).
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    # No incluir el token "jti" en el access (no lo necesitamos).
    "JTI_CLAIM": "jti",
    # Nombre de la cookie donde pondremos el refresh token.
    "AUTH_COOKIE": "refresh_token",
    # Path de la cookie: solo se envía a endpoints bajo /api/auth/.
    "AUTH_COOKIE_PATH": "/api/auth/",
    # HttpOnly: JS no puede leerla (a prueba de XSS).
    "AUTH_COOKIE_HTTP_ONLY": True,
    # SameSite: Lax (no se envía en POST cross-site → protege de CSRF).
    "AUTH_COOKIE_SAMESITE": "Lax",
    # Secure: en base False; en producción.py lo forzamos a True.
    "AUTH_COOKIE_SECURE": False,
}


# ============================================================
# LOGGING ESTRUCTURADO
# ============================================================

LOGGING = {
    "version": 1,
    # Desactiva loggers preexistentes (los nuestros sustituyen).
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        # Logger propio para errores de API.
        "api.errors": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
