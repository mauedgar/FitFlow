# app/crud/crud_class_schedule.py
from app.crud.base import CRUDBase
from app.models import ClassSchedule
from app.schemas import ClassScheduleCreate, ClassScheduleUpdate

class CRUDClassSchedule(CRUDBase[ClassSchedule, ClassScheduleCreate, ClassScheduleUpdate]):
    # Por ahora, el CRUD base es suficiente para crear, leer, actualizar, eliminar.
    # Podrías añadir métodos específicos aquí si necesitaras lógicas de búsqueda complejas
    # o validaciones adicionales antes de crear/actualizar.
    pass

class_schedule = CRUDClassSchedule(ClassSchedule)