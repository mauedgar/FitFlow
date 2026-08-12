# app/crud/crud_permission.py
from app.crud.base import CRUDBase
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate

permission = CRUDBase[Permission, PermissionCreate, PermissionUpdate](Permission)

