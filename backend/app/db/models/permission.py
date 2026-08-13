"""Contrato legacy no persistente para RBAC granular futuro."""

from dataclasses import dataclass


@dataclass(slots=True)
class Permission:
    """Permiso no ORM; la autorización vigente usa ``UserRole``."""

    id: str
    description: str | None = None
