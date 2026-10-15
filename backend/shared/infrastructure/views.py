"""
Vistas compartidas (health check, versión).
"""

# `permissions` de DRF: controla quién accede.
from rest_framework import permissions

# `Request` es el tipo del objeto request que DRF pasa a las vistas.
from rest_framework.request import Request

# `Response` = respuesta HTTP de DRF.
from rest_framework.response import Response

# `APIView` = vista base de DRF.
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    GET /api/health/ → 200 {"status": "ok"}.

    Útil para verificar manualmente, para balanceadores en Fase 7 y para
    tests de humo.
    """

    # Permite acceso sin autenticación.
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        """
        Responde a GET /api/health/.

        Args:
            request: petición HTTP de DRF.

        Returns:
            Respuesta JSON con {"status": "ok"}.
        """
        return Response({"status": "ok"})
