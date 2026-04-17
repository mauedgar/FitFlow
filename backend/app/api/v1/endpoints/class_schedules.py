# app/api/endpoints/class_schedules.py
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from app import crud, schemas
from app.db.session import get_db
from app.models.class_schedule import ClassSchedule
#from app.models.class_session import ClassSession # Para futuras sesiones

router = APIRouter()

@router.post("/", response_model=schemas.ClassSchedule, status_code=status.HTTP_201_CREATED)
def create_class_schedule(
    *,
    db: Session = Depends(get_db),
    schedule_in: schemas.ClassScheduleCreate
):
    """
    Crea una nueva oferta de horario recurrente para una clase con un profesor.
    """
    # 1. Validar que gym_class_id y teacher_id existen
    gym_class = crud.gym_class.get(db, id=schedule_in.gym_class_id)
    if not gym_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La clase con id {schedule_in.gym_class_id} no fue encontrada.",
        )
    
    teacher = crud.teacher.get(db, id=schedule_in.teacher_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El profesor con id {schedule_in.teacher_id} no fue encontrado.",
        )
    
    # 2. Crear el ClassSchedule
    new_schedule = crud.class_schedule.create(db=db, obj_in=schedule_in)
    
    return new_schedule

@router.get("/", response_model=List[schemas.ClassSchedule])
def read_class_schedules(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    gym_class_id: Optional[uuid.UUID] = None, # Filtro opcional por clase
    teacher_id: Optional[uuid.UUID] = None,  # Filtro opcional por profesor
):
    """
    Obtiene una lista de ofertas de horarios de clases, con su clase y profesor asociados.
    Permite filtrar por gym_class_id o teacher_id.
    """
    query = db.query(ClassSchedule).options(
        selectinload(ClassSchedule.gym_class),
        selectinload(ClassSchedule.teacher)
    )

    if gym_class_id:
        query = query.filter(ClassSchedule.gym_class_id == gym_class_id)
    if teacher_id:
        query = query.filter(ClassSchedule.teacher_id == teacher_id)

    class_schedules = query.offset(skip).limit(limit).all()
    return class_schedules

@router.get("/{schedule_id}", response_model=schemas.ClassSchedule)
def read_class_schedule_by_id(
    *,
    db: Session = Depends(get_db),
    schedule_id: uuid.UUID
):
    """
    Obtiene los detalles de una oferta de horario de clase específica por su ID.
    Incluye la clase, el profesor y las sesiones futuras asociadas.
    """
    # Cargamos gym_class, teacher y las sesiones futuras (ej. las próximas 30 sesiones o hasta fin de mes)
    # Aquí puedes añadir lógica para generar sesiones si aún no existen
    schedule = (
        db.query(ClassSchedule)
        .options(
            selectinload(ClassSchedule.gym_class),
            selectinload(ClassSchedule.teacher),
            # Podrías cargar las sesiones existentes o generarlas/filtrarlas en el servicio
            selectinload(ClassSchedule.sessions) 
        )
        .filter(ClassSchedule.id == schedule_id)
        .first()
    )
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La oferta de horario con id {schedule_id} no fue encontrada.",
        )
    
    # TODO: Lógica para filtrar 'future_sessions' si es necesario, o generarlas
    # Por ahora, el schema las mapeará si están cargadas o como lista vacía.

    return schedule

# Endpoints para actualizar y eliminar ClassSchedule
@router.put("/{schedule_id}", response_model=schemas.ClassSchedule)
def update_class_schedule(
    *,
    db: Session = Depends(get_db),
    schedule_id: uuid.UUID,
    schedule_in: schemas.ClassScheduleUpdate
):
    class_schedule = crud.class_schedule.get(db, id=schedule_id)
    if not class_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La oferta de horario con id {schedule_id} no fue encontrada.",
        )
    # Aquí puedes añadir validación adicional si se cambian gym_class_id o teacher_id
    class_schedule = crud.class_schedule.update(db, db_obj=class_schedule, obj_in=schedule_in)
    return class_schedule

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class_schedule(
    *,
    db: Session = Depends(get_db),
    schedule_id: uuid.UUID
):
    class_schedule = crud.class_schedule.get(db, id=schedule_id)
    if not class_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La oferta de horario con id {schedule_id} no fue encontrada.",
        )
    crud.class_schedule.remove(db, id=schedule_id)
    return {"message": "Oferta de horario eliminada exitosamente."}
