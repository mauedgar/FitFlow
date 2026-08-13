"""Contrato legacy no persistente para RBAC granular futuro."""

from dataclasses import dataclass


@dataclass(slots=True)
class Role:
    """Rol no ORM; la autorización vigente usa ``UserRole``."""

    id: str
    description: str | None = None
