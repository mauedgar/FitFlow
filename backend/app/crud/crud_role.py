# app/crud/crud_role.py
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate

from .base import CRUDBase

role = CRUDBase[Role, RoleCreate, RoleUpdate](Role)
