# app/api/endpoints/class_sessions.py
from typing import List, Optional
import uuid
from datetime import date, time, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from app import crud, schemas
from app.db.session import get_db
from app.models.class_session import ClassSession
from app.models.class_schedule import ClassSchedule

router = APIRouter()

# Este endpoint podría ser para la creación manual de una sesión,
# pero lo más común es que se generen automáticamente.
@router.post("/", response_model=schemas.ClassSession, status_code=status.HTTP_201_CREATED)
def create_class_session(
    *,
    db: Session = Depends(get_db),
    session_in: schemas.ClassSessionCreate
):
    """
    Crea una nueva sesión de clase. Principalmente para uso interno o administrativo.
    """
    class_schedule = crud.class_schedule.get(db, id=session_in.class_schedule_id)
    if not class_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La oferta de horario con id {session_in.class_schedule_id} no fue encontrada.",
        )
    
    new_session = crud.class_session.create(db=db, obj_in=session_in)
    return new_session


@router.get("/", response_model=List[schemas.ClassSession])
def read_class_sessions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    class_schedule_id: Optional[uuid.UUID] = None,
    gym_class_id: Optional[uuid.UUID] = None, # Filtrar por la clase base
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    include_cancelled: bool = False
):
    """
    Obtiene una lista de sesiones de clase, con su horario y clase asociados.
    Permite filtrar por schedule, clase, rango de fechas y si incluir las canceladas.
    """
    query = (
        db.query(ClassSession)
        .options(
            selectinload(ClassSession.class_schedule).selectinload(ClassSchedule.gym_class),
            selectinload(ClassSession.class_schedule).selectinload(ClassSchedule.teacher),
            selectinload(ClassSession.bookings) # Para contar las reservas
        )
    )

    if class_schedule_id:
        query = query.filter(ClassSession.class_schedule_id == class_schedule_id)
    if gym_class_id:
        # Se necesita un join para filtrar por GymClass ID
        query = query.join(ClassSchedule).filter(ClassSchedule.gym_class_id == gym_class_id)
   # --- FILTROS DE FECHA REVISADOS ---
    if from_date:
        # Compara el inicio del día
        start_of_day = datetime.combine(from_date, time.min)
        query = query.filter(ClassSession.starts_at >= start_of_day)
    if to_date:
        # Compara el final del día
        end_of_day = datetime.combine(to_date, time.max)
        query = query.filter(ClassSession.starts_at <= end_of_day)
        
    if not include_cancelled:
        query = query.filter(ClassSession.status == False) # Más explícito  # noqa: E712

    query = query.order_by(ClassSession.starts_at)    

    sessions = query.offset(skip).limit(limit).all()
    
    # Calcular disponibilidad
    for session in sessions:
        session.current_bookings_count = len(session.bookings)
        session.available_spots = session.class_schedule.capacity - session.current_bookings_count
    
    print(f"✅ Query encontró {len(sessions)} sesiones.")

    return sessions

@router.get("/{session_id}", response_model=schemas.ClassSession)
def read_class_session_by_id(
    *,
    db: Session = Depends(get_db),
    session_id: uuid.UUID
):
    """
    Obtiene los detalles de una sesión de clase específica por su ID,
    incluyendo su horario, clase, profesor y estado de reserva.
    """
    session = (
        db.query(ClassSession)
        .options(
            selectinload(ClassSession.class_schedule).selectinload(ClassSchedule.gym_class),
            selectinload(ClassSession.class_schedule).selectinload(ClassSchedule.teacher),
            selectinload(ClassSession.bookings)
        )
        .filter(ClassSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La sesión de clase con id {session_id} no fue encontrada.",
        )
    
    # Calcular disponibilidad para la sesión individual
    session.current_bookings_count = len(session.bookings)
    session.available_spots = session.class_schedule.capacity - session.current_bookings_count
    
    return session

@router.put("/{session_id}", response_model=schemas.ClassSession)
def update_class_session(
    *,
    db: Session = Depends(get_db),
    session_id: uuid.UUID,
    session_in: schemas.ClassSessionUpdate
):
    class_session = crud.class_session.get(db, id=session_id)
    if not class_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La sesión de clase con id {session_id} no fue encontrada.",
        )
    class_session = crud.class_session.update(db, db_obj=class_session, obj_in=session_in)
    return class_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class_session(
    *,
    db: Session = Depends(get_db),
    session_id: uuid.UUID
):
    class_session = crud.class_session.get(db, id=session_id)
    if not class_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La sesión de clase con id {session_id} no fue encontrada.",
        )
    crud.class_session.remove(db, id=session_id)
    return {"message": "Sesión de clase eliminada exitosamente."}
