from datetime import date, datetime, timedelta
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

# =============================================================================
# IMPORTS: Separamos claramente los Modelos (BD) de los Esquemas (API)
# =============================================================================
from app import crud, schemas, models
from app.db.session import get_db
from app.models.class_schedule import ClassSchedule


router = APIRouter()

@router.post("/", response_model=schemas.GymClass, status_code=status.HTTP_201_CREATED)
def create_gym_class(
    *,
    db: Session = Depends(get_db),
    class_in: schemas.GymClassCreate
):
    """
    Crea una nueva clase de gimnasio.
    Los profesores y horarios se asociarán a través de ClassSchedule.
    """
    new_class = crud.gym_class.create(db=db, obj_in=class_in)
    return new_class


@router.get("/", response_model=List[schemas.GymClass])
def read_gym_classes(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Obtiene una lista de clases de gimnasio, incluyendo sus ofertas de horarios.
    """
    gym_classes = (
        db.query(crud.gym_class.model)
        .options(
            selectinload(crud.gym_class.model.class_schedules).selectinload(ClassSchedule.teacher)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )    
    return gym_classes

@router.get("/{class_id}", response_model=schemas.GymClassWithSchedules)
def read_gym_class_by_id(
    *,
    db: Session = Depends(get_db),
    class_id: uuid.UUID
):
    """
    ENDPOINT PRINCIPAL: Obtiene los detalles de una clase y calcula información
    de disponibilidad en tiempo real para cada horario.
    
    Este endpoint implementa la lógica de "next_upcoming_session" que el frontend
    necesita para mostrar botones inteligentes y badges de disponibilidad.
    """
    # -------------------------------------------------------------------------
    # 1. CONSULTA PRINCIPAL: Obtener la clase con sus horarios y profesores
    # -------------------------------------------------------------------------
    gym_class = db.query(crud.gym_class.model).options(
        selectinload(crud.gym_class.model.class_schedules)
        .selectinload(ClassSchedule.teacher)
    ).filter(models.GymClass.id == class_id).first()

    if not gym_class:
        raise HTTPException(status_code=404, detail="Clase no encontrada")

    # -------------------------------------------------------------------------
    # 2. LÓGICA DE ENRIQUECIMIENTO: Para cada horario, calcular próxima sesión
    # -------------------------------------------------------------------------
    for schedule in gym_class.class_schedules:
        today = date.today()
        next_session_info = None
        
        # Buscar la próxima fecha de clase en los siguientes 60 días
        for i in range(60):
            current_date = today + timedelta(days=i)
            
            # Verificar si este día coincide con los días de la semana del horario
            # weekday(): Lunes=0, Martes=1, ..., Domingo=6
            if current_date.weekday() in schedule.days_of_week:
                # ¡Encontramos una fecha válida! Ahora verificamos disponibilidad
                start_dt = datetime.combine(current_date, schedule.start_time)
                
                # CORRECCIÓN CLAVE: Usar models.ClassSession en TODA la consulta
                # Buscar si ya existe una ClassSession para esa fecha y hora exactas
                session = db.query(models.ClassSession).filter(
                    models.ClassSession.class_schedule_id == schedule.id,  # 👈 CORRECCIÓN
                    models.ClassSession.start_datetime == start_dt          # 👈 CORRECCIÓN
                ).options(selectinload(models.ClassSession.bookings)).first()
                
                if session:
                    # La sesión ya existe: contar reservas confirmadas
                    bookings_count = len([
                        b for b in session.bookings 
                        if b.status == 'CONFIRMED'
                    ])
                    available_spots = schedule.max_capacity - bookings_count
                else:
                    # La sesión no existe: todos los cupos están disponibles
                    available_spots = schedule.max_capacity

                # Preparar la información que el frontend necesita
                next_session_info = {
                    "start_datetime": start_dt,
                    "available_spots": available_spots
                }
                break  # Salimos del bucle: ya encontramos la primera fecha disponible

        # -------------------------------------------------------------------------
        # 3. INYECCIÓN DE DATOS: Añadir la info calculada al objeto del horario
        # -------------------------------------------------------------------------
        # Esta es la "magia": FastAPI/Pydantic detectará automáticamente este
        # atributo y lo incluirá en la respuesta JSON, aunque no esté definido
        # en el modelo de SQLAlchemy original.
        schedule.next_upcoming_session = next_session_info

    return gym_class

@router.put("/{class_id}", response_model=schemas.GymClass)
def update_gym_class(
    *,
    db: Session = Depends(get_db),
    class_id: uuid.UUID,
    class_in: schemas.GymClassUpdate
):
    """
    Actualiza una clase de gimnasio existente.
    """
    gym_class = crud.gym_class.get(db, id=class_id)
    if not gym_class:
        raise HTTPException(
            status_code=404,
            detail=f"La clase con id {class_id} no fue encontrada."
        )
    gym_class = crud.gym_class.update(db, db_obj=gym_class, obj_in=class_in)
    return gym_class

@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gym_class(
    *,
    db: Session = Depends(get_db),
    class_id: uuid.UUID
):
    """
    Elimina una clase de gimnasio y todos sus horarios asociados.
    """
    gym_class = crud.gym_class.get(db, id=class_id)
    if not gym_class:
        raise HTTPException(
            status_code=404,
            detail=f"La clase con id {class_id} no fue encontrada."
        )
    crud.gym_class.remove(db, id=class_id)
    return {"message": "Clase eliminada exitosamente."}