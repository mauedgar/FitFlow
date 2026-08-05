# app/crud/crud_permission.py
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate

from .base import CRUDBase

permission = CRUDBase[Permission, PermissionCreate, PermissionUpdate](Permission)
