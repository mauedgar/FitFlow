"""Errores de dominio y utilitarios para los servicios.

Contiene excepciones ligeras y específicas que los servicios y el CRUD
pueden lanzar. Los routers deben capturarlas y mapearlas a HTTPException.
"""

from __future__ import annotations


class DomainError(Exception):
    """Error base para la capa de dominio / servicios."""


class NotFoundError(DomainError):
    """Recurso no encontrado."""


class BusinessValidationError(DomainError):
    """Falla de validación de negocio (entrada válida pero regla de negocio incumplida)."""


class ConflictError(DomainError):
    """Conflicto de estado (duplicado, overbooking, constraint violada)."""


class PermissionDeniedError(DomainError):
    """Acceso denegado por permisos o propiedad del recurso."""


class AuthError(DomainError):
    """Errores relacionados con autenticación / tokens."""


class ExternalServiceError(DomainError):
    """Fallo al comunicarse con un servicio externo (Redis, email, etc.)."""


__all__ = [
    "AuthError",
    "BusinessValidationError",
    "ConflictError",
    "DomainError",
    "ExternalServiceError",
    "NotFoundError",
    "PermissionDeniedError",
]
