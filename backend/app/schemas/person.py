"""Schemas para Person (Sprint 6-7).

--------------------------------
Incluye:
• PersonBase
• PersonCreate
• PersonUpdate (todos opcionales)
"""
# ruff: noqa: PIE790
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# --------------------------------------------------------------------------- #
# 1. Base
# --------------------------------------------------------------------------- #

class PersonBase(BaseModel):
    """Campos comunes de identidad personal.

    Usado por Client y Teacher.
    """

    first_name: str
    last_name: str
    document_number: str | None = None
    address: str | None = None
    medical_fit_url: str | None = None
    profile_image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- #
# 2. Creación
# --------------------------------------------------------------------------- #

class PersonCreate(PersonBase):
    """Esquema para crear una persona.

    Todos los campos obligatorios vienen de PersonBase.
    """

    pass


# --------------------------------------------------------------------------- #
# 3. Actualización (todos opcionales)
# --------------------------------------------------------------------------- #

class PersonUpdate(BaseModel):
    """Esquema para actualizar parcialmente una persona.

    TODOS los campos son opcionales.
    Esto permite PATCH sin romper modelos derivados.
    """

    first_name: str | None = None
    last_name: str | None = None
    document_number: str | None = None
    address: str | None = None
    medical_fit_url: str | None = None
    profile_image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
