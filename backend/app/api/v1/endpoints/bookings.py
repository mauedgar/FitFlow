# app/api/endpoints/bookings.py
from typing import List
import uuid
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app import crud, schemas
from app.db.session import get_db
from app.models.booking import Booking, BookingStatus
from app.models.class_session import ClassSession
from app.models.class_schedule import ClassSchedule
#from app.models.client import Client # Asume que tienes un crud.client
from app.models.user import User # Asume que tienes un modelo User para autenticación

# Asume que tienes un mecanismo de autenticación para obtener el usuario actual
#from app.api.deps import get_current_active_client # <-- Necesitarás implementar esto
from app.api.deps import get_current_active_user 

router = APIRouter()

@router.post("/", response_model=schemas.Booking, status_code=status.HTTP_201_CREATED)
def create_booking(
    *,
    db: Session = Depends(get_db),
    booking_in: schemas.BookingCreate, # Contiene class_session_id
    current_user: User = Depends(get_current_active_user) # Asume que User tiene un person_profile
):
    """
    Crea una nueva reserva.
    - Si se provee `class_session_id`, crea una única reserva.
    - Si se provee `class_schedule_id`, crea reservas recurrentes para el cliente.
    Solo clientes autenticados pueden reservar.
    """

    # 1. Verificar que el usuario autenticado sea un cliente
    client = crud.client.get_by_user_id(db, user_id=current_user.id) # Necesitarás este método en crud.client
    if not client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los clientes pueden realizar reservas.",
        )
    # =============================================================================
    # CASO 1: RESERVA DE UNA ÚNICA SESIÓN (LÓGICA ANTIGUA)
    # =============================================================================
    if booking_in.class_session_id:
        # 2. Obtener la ClassSession y su ClassSchedule para verificar la capacidad
        class_session = crud.class_session.get(db, id=booking_in.class_session_id)

        if not class_session:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail="Sesión de clase no encontrada.")
            
        if class_session.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta sesión de clase ha sido cancelada y no se pueden realizar reservas.",
            )

        # 3. Verificar que la clase no haya alcanzado su capacidad máxima
        # Contar las reservas confirmadas para esta sesión   

        current_bookings_count = db.query(Booking).filter(
            Booking.class_session_id == booking_in.class_session_id,
            Booking.status == BookingStatus.CONFIRMED # Solo contamos confirmadas
        ).count()    
    
        if current_bookings_count >= class_session.class_schedule.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta sesión de clase ya está llena. No hay cupos disponibles.",
            )        

        # 4. Verificar que el cliente no tenga ya una reserva para esa sesión
        existing_booking = db.query(Booking).filter(
            Booking.client_id == client.id,
            Booking.class_session_id == booking_in.class_session_id,
            Booking.status != BookingStatus.CANCELLED # Si hay una booking cancelada, podría reservar de nuevo
        ).first()
        if existing_booking:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya tienes una reserva activa para esta sesión de clase.",
            )

        # 5. Crear el registro de Booking
        booking_data = {
            "client_id": client.id,
            "class_session_id": booking_in.class_session_id,
            "created_at": datetime.now(),
            "status": BookingStatus.PENDING, # Puedes cambiar a PENDING si hay un flujo de pago
        }
        new_booking = crud.booking.create(db=db, obj_in=schemas.BookingCreateInternal(**booking_data)) # Asegúrate que crud.booking.create maneja dict
        
        # Reload the booking to get related objects for the response schema
        db.refresh(new_booking)
        # Ensure nested objects are loaded for the response
        new_booking = (
            db.query(Booking)
            .options(
                selectinload(Booking.client),
                selectinload(Booking.class_session)
                .selectinload(ClassSession.class_schedule)
                .selectinload(ClassSchedule.gym_class),
                selectinload(Booking.class_session)
                .selectinload(ClassSession.class_schedule)
                .selectinload(ClassSchedule.teacher)
            )
            .filter(Booking.id == new_booking.id)
            .first()
        )

        return new_booking
    
     # =============================================================================
    # CASO 2: RESERVA RECURRENTE POR HORARIO (NUEVA LÓGICA)
    # =============================================================================
    if booking_in.class_schedule_id:
        schedule = crud.class_schedule.get(db, id=booking_in.class_schedule_id)
        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario de clase no encontrado.")

        # ASUNCIÓN: Obtenemos la fecha de fin de la membresía del cliente.
        # Necesitarás una lógica para esto. Ejemplo:
        if not client.active_membership or client.active_membership.end_date < date.today():
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes una membresía activa para reservar.")
        
        start_date = date.today()
        end_date = date.today() + timedelta(7)#client.active_membership.end_date
        
        # 1. Calcular todas las fechas de clase dentro del período de la membresía
        target_dates = []
        current_date = start_date
        while current_date <= end_date:
            # weekday() -> Lunes=0, Domingo=6
            if current_date.weekday() in schedule.days_of_week:
                target_dates.append(current_date)
            current_date += timedelta(days=1)
        
        if not target_dates:
            raise HTTPException(status_code=400, detail="No hay clases programadas para este horario en el período de tu membresía.")

        # 2. Iniciar una transacción: O se crean todas las reservas, o no se crea ninguna.
        first_created_booking = None
        created_count = 0
        try:
            for class_date in target_dates:
                # 3. Para cada fecha, encontrar o crear la ClassSession
                starts_at = datetime.combine(class_date, schedule.start_time)
                ends_at = datetime.combine(class_date, schedule.duration_minutes)

                # Usamos un helper get_or_create para evitar duplicados
                session, _ = crud.class_session.get_or_create(
                    db,
                    class_schedule_id=schedule.id,
                    starts_at=starts_at,
                    defaults={'ends_at': ends_at}
                )

                # 4. Validar capacidad y si ya existe reserva para esta sesión específica
                current_bookings_count = len([b for b in session.bookings if b.status == BookingStatus.CONFIRMED])
                if current_bookings_count >= schedule.capacity:
                    continue # Hay cupo lleno, saltamos a la siguiente fecha

                already_booked = any(b.client_id == client.id and b.status != BookingStatus.CANCELLED for b in session.bookings)
                if already_booked:
                    continue # El usuario ya está en esta sesión, saltamos

                # 5. Crear la reserva
                booking_data = { "client_id": client.id, "class_session_id": session.id }
                new_booking = crud.booking.create_with_defaults(db, obj_in=booking_data)
                created_count += 1
                if not first_created_booking:
                    first_created_booking = new_booking
            
            if created_count == 0:
                raise HTTPException(status_code=409, detail="No se encontraron cupos disponibles para las fechas de tu membresía.")

            db.commit()

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Ocurrió un error al procesar las reservas: {e}")

        # 6. Recargar el primer booking para la respuesta con todas las relaciones
        db.refresh(first_created_booking)
        # (Aquí la misma lógica para cargar las relaciones que tenías antes)
        
        return first_created_booking

@router.get("/me", response_model=List[schemas.Booking])
def read_my_bookings(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene todas las reservas del cliente autenticado.
    """
    client = crud.client.get_by_user_id(db, user_id=current_user.id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los clientes pueden ver sus reservas.",
        )
    
    bookings = (
        db.query(Booking)
        .options(
            selectinload(Booking.class_session)
            .selectinload(ClassSession.class_schedule)
            .selectinload(ClassSchedule.gym_class),
            selectinload(Booking.class_session)
            .selectinload(ClassSession.class_schedule)
            .selectinload(ClassSchedule.teacher)
        )
        .filter(Booking.client_id == client.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return bookings

@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(
    *,
    db: Session = Depends(get_db),
    booking_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancela una reserva existente. Solo el cliente que realizó la reserva puede cancelarla.
    """
    client = crud.client.get_by_user_id(db, user_id=current_user.id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Solo los clientes pueden cancelar sus reservas.",
        )

    booking = crud.booking.get(db, id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La reserva con id {booking_id} no fue encontrada.",
        )

    if booking.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar esta reserva.",
        )
    
    if booking.status == BookingStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta reserva ya ha sido cancelada previamente.",
        )

    # Actualizar el estado de la reserva a CANCELLED
    booking_update_data = schemas.BookingUpdate(status=BookingStatus.CANCELLED.value)
    crud.booking.update(db, db_obj=booking, obj_in=booking_update_data)
    
    return {"message": "Reserva cancelada exitosamente."}
