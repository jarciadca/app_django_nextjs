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
