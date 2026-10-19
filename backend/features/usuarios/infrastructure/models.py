"""
Modelos Django del slice `usuarios`.

Aquí vive la capa de infraestructura del dominio usuarios: tablas, columnas
e índices. Los modelos son "tontos" (solo estructura); las reglas de negocio
están en domain/ y application/.

Modelos:
    - Usuario: custom user que sustituye a django.contrib.auth.User.
    - PasswordResetToken: tokens de recuperación de contraseña.
"""

import uuid
from datetime import datetime, timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UsuarioManager(BaseUserManager["Usuario"]):
    """
    Manager para el modelo Usuario.

    Django usa `objects = UsuarioManager()` para saber cómo crear usuarios
    y superusuarios. Necesario porque heredamos de AbstractBaseUser (no de
    AbstractUser, que ya trae su manager).
    """

    # use_in_migrations: el manager se serializa en las migraciones.
    use_in_migrations = True

    def _create_user(
        self,
        username: str,
        email: str,
        password: str | None,
        **extra_fields: object,
    ) -> "Usuario":
        """Crea y guarda un usuario con la contraseña hasheada."""
        # Validación mínima de username.
        if not username:
            raise ValueError("El username es obligatorio.")
        if not email:
            raise ValueError("El email es obligatorio.")

        # Normalización: email en minúsculas, username tal cual (case-sensitive).
        email = self.normalize_email(email)

        # Creamos la instancia (sin guardar aún).
        user = self.model(username=username, email=email, **extra_fields)

        # set_password hashea la contraseña (nunca se guarda en claro).
        # Si password es None, marca la contraseña como "no usable".
        user.set_password(password)

        # Persistimos en la BD.
        user.save(using=self._db)
        return user

    def create_user(
        self,
        username: str,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> "Usuario":
        """Crea un usuario normal (is_staff=False, is_superuser=False)."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(
        self,
        username: str,
        email: str,
        password: str | None = None,
        **extra_fields: object,
    ) -> "Usuario":
        """Crea un superusuario (para `manage.py createsuperuser`)."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model del proyecto.

    Sustituye a django.contrib.auth.models.User. Usamos username como
    identificador de login (según decisión de Fase 3) y email como dato
    de contacto único.

    Attributes:
        id: UUID primario (más seguro que autoincremental para exponer en URLs).
        username: identificador de login, único, case-sensitive.
        email: email único, normalizado a minúsculas.
        first_name, last_name: nombre y apellidos (opcionales).
        is_active: si False, el usuario no puede autenticarse.
        is_staff: si True, puede entrar al admin de Django.
        is_superuser: si True, tiene todos los permisos.
        date_joined: fecha de alta.
        last_login: última vez que se autenticó (lo actualiza Django).
    """

    # UUID como PK: no expone el orden de creación y es más difícil de enumerar.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Username: identificador de login. Unique, indexado.
    username = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        help_text="Identificador de login. Solo letras, números y @/./+/-/_.",
        error_messages={"unique": "Ya existe un usuario con ese username."},
    )

    # Email: único, indexado, normalizado a minúsculas.
    email = models.EmailField(
        unique=True,
        db_index=True,
        error_messages={"unique": "Ya existe un usuario con ese email."},
    )

    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    # is_active=False impide el login (útil para bans o cuentas sin verificar).
    is_active = models.BooleanField(default=True)

    # is_staff=True permite entrar al admin de Django.
    is_staff = models.BooleanField(default=False)

    # is_superuser viene de PermissionsMixin.

    date_joined = models.DateTimeField(default=timezone.now)

    # Sobreescribimos last_login porque AbstractBaseUser ya lo trae, pero
    # queremos que sea nullable (usuarios recién creados no han hecho login).
    last_login = models.DateTimeField(null=True, blank=True)

    # Manager personalizado.
    objects = UsuarioManager()

    # Campo usado como "username" por Django internamente.
    USERNAME_FIELD = "username"

    # Campos obligatorios al crear un superusuario por CLI (además de password).
    REQUIRED_FIELDS = ["email"]

    class Meta:
        # Nombre de la tabla en la BD.
        db_table = "usuarios_usuario"
        # Nombre legible en el admin.
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        # Orden por defecto de los querysets.
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        """Representación legible para admin y logs."""
        return self.username

    def get_full_name(self) -> str:
        """Nombre completo si está disponible; si no, username."""
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    def get_short_name(self) -> str:
        """Nombre corto (username por ahora)."""
        return self.username


class PasswordResetToken(models.Model):
    """
    Token de recuperación de contraseña.

    Flujo:
        1. El usuario solicita reset con su email.
        2. Se genera un token aleatorio (64 hex chars) y se envía por email.
        3. Se guarda SOLO el hash sha256 del token en la BD.
        4. El usuario hace clic en el enlace con el token en claro.
        5. El backend hashea el token recibido y busca por `token_hash`.
        6. Si existe y no ha expirado ni se ha usado, permite cambiar la contraseña.
        7. Se marca `used_at` para invalidar el token.

    Por qué guardamos el hash y no el token en claro:
        Si la BD se filtra, el atacante no puede usar los tokens porque
        no tiene la preimagen del hash.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # FK al usuario. on_delete=CASCADE: si se borra el usuario, sus tokens también.
    user = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )

    # Hash sha256 (64 chars hex) del token enviado al usuario.
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # Fecha de expiración: 24h por defecto desde la creación.
    expires_at = models.DateTimeField()

    # Null = token no usado. Fecha = token ya consumido (no se puede reutilizar).
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "usuarios_password_reset_token"
        verbose_name = "token de reset de contraseña"
        verbose_name_plural = "tokens de reset de contraseña"
        ordering = ["-created_at"]
        indexes = [
            # Índice para buscar tokens vigentes de un usuario rápidamente.
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        """Representación legible: usuario + estado."""
        estado = "usado" if self.used_at else "vigente"
        return f"Reset token de {self.user.username} ({estado})"

    @property
    def is_expired(self) -> bool:
        """True si ha pasado la fecha de expiración."""
        return timezone.now() > self.expires_at

    @property
    def is_usable(self) -> bool:
        """True si el token puede usarse (no expirado y no consumido)."""
        return self.used_at is None and not self.is_expired

    @classmethod
    def default_expiration(cls) -> datetime:
        """Helper para calcular la fecha de expiración por defecto."""
        return timezone.now() + timedelta(hours=24)
