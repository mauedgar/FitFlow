from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
# Importamos ClassSchedule para poder obtenerlo junto con Teacher
from app.models.class_schedule import ClassSchedule
from app.models.gym_class import GymClass # Si necesitamos cargar la GymClass anidada
from app import crud, schemas
from app.db.session import get_db
from app.models.user import User, UserRole # Importar tu modelo User y UserRole
from app.api.deps import (
    get_current_active_user,
    get_current_active_admin,
    get_current_active_trainer,
    get_current_active_admin_or_self
)


router = APIRouter()
# Este endpoint asume que un 'User' ya existe y le vamos a crear
# su perfil de 'Teacher' (que hereda de 'Person').

# --- Endpoints de Creación y Modificación (Normalmente para Admins o con validación estricta) ---

@router.post("/{user_id}", response_model=schemas.Teacher, status_code=status.HTTP_201_CREATED)
def create_teacher_for_user(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    teacher_in: schemas.TeacherCreate,
    current_user: User = Depends(get_current_active_admin)     
):
    """
    Crea un perfil de profesor para un usuario existente.
    Requiere permisos de administrador.
    """
    # 1. Verificar que el usuario al que le crearemos el perfil existe
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario con id {user_id} no fue encontrado.",
        )
    
    # 2. Verificar que este usuario no tenga ya un perfil de persona
    #    (La relación User->Person es uno-a-uno)
    if user.person_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El usuario con id {user_id} ya tiene un perfil asociado.",
        )
    # ⭐ Asegurarse de que el usuario tenga el rol TRAINER si le asignas un perfil de profesor
    if user.role != UserRole.TRAINER:
         # Podrías decidir cambiar el rol del usuario aquí o levantar una excepción
         # user.role = UserRole.TRAINER
         # db.add(user)
         # db.commit()
         # db.refresh(user)
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail=f"El usuario con id {user_id} no tiene el rol de {UserRole.TRAINER}. Por favor, actualiza el rol del usuario primero."
         )
    # 3. Usar el CRUD para crear el perfil de profesor y asociarlo
    teacher = crud.teacher.create_with_user(db=db, obj_in=teacher_in, user=user)
    
    return teacher

# --- Endpoints de Lectura (Pueden ser públicos o para usuarios autenticados) ---

@router.get("/", response_model=List[schemas.Teacher])
def read_teachers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Obtiene una lista de profesores, incluyendo las ofertas de horarios que imparten.
    """
    # Cargamos las class_schedules de cada Teacher y la GymClass asociada a cada ClassSchedule
    teachers = (
        db.query(crud.teacher.model)
        .options(
            selectinload(crud.teacher.model.class_schedules)
            .selectinload(ClassSchedule.gym_class)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return teachers

@router.get("/{teacher_id}", response_model=schemas.Teacher)
def read_teacher_by_id(
    *,
    db: Session = Depends(get_db),
    teacher_id: uuid.UUID,
    # ⭐ Un admin puede ver cualquier perfil, un trainer solo el suyo
    # current_user: User = Depends(get_current_active_admin_or_self(requested_id=teacher_id)) # Adaptar si get_current_active_admin_or_self no recibe id
    current_user: User = Depends(get_current_active_user) # Versión simplificada
):
    """
    Obtiene los detalles de un profesor específico por su ID,
    incluyendo las ofertas de horarios que imparte y las clases asociadas.
    """
    teacher = (
        db.query(crud.teacher.model)
        .options(
            selectinload(crud.teacher.model.class_schedules)
            .selectinload(ClassSchedule.gym_class)
        )
        .filter(crud.teacher.model.id == teacher_id)
        .first()
    )
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El profesor con id {teacher_id} no fue encontrado.",
        )
    return teacher

# --- Endpoints de Actualización y Borrado (Normalmente para Admins o el propio profesor) ---

@router.put("/{teacher_id}", response_model=schemas.Teacher)
def update_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_id: uuid.UUID,
    teacher_in: schemas.TeacherUpdate,
    # ⭐ Solo un administrador puede actualizar cualquier perfil de profesor, o el propio profesor el suyo.
    current_user: User = Depends(get_current_active_user) # Usamos la dependencia base y luego validamos
):
    """
    Actualiza el perfil de un profesor. Requiere permisos de administrador o ser el propio profesor.
    """
    teacher = crud.teacher.get(db, id=teacher_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El profesor con id {teacher_id} no fue encontrado.",
        )
    
    # Lógica de autorización: Admin o el propio profesor
    if current_user.role != UserRole.ADMIN:
        if not current_user.person_profile or current_user.person_profile.id != teacher_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para actualizar este perfil de profesor.")
        
        # Si no es admin y es el propio profesor, quizás no pueda cambiar ciertos campos
        # Por ejemplo, un profesor no debería poder cambiar su CUIL o rol desde aquí.
        # Puedes añadir lógica aquí para filtrar `teacher_in` si no es admin.
        if teacher_in.cuil is not None or teacher_in.email is not None: # Ejemplo de campos restringidos
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para actualizar el CUIL o email de tu perfil.")

    updated_teacher = crud.teacher.update(db, db_obj=teacher, obj_in=teacher_in)
    return updated_teacher

@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(
    *,
    db: Session = Depends(get_db),
    teacher_id: uuid.UUID,
    # ⭐ Solo un administrador puede borrar perfiles de profesor
    current_user: User = Depends(get_current_active_admin) 
):
    """
    Elimina un perfil de profesor. Requiere permisos de administrador.
    """
    teacher = crud.teacher.get(db, id=teacher_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El profesor con id {teacher_id} no fue encontrado.",
        )
    
    # Antes de eliminar el perfil de persona, puedes decidir si también quieres eliminar el User asociado
    # o solo desvincularlo y cambiar su rol, o poner el User como inactivo.
    user_to_update = crud.user.get(db, id=teacher.user.id) # Suponiendo que Teacher tiene una relación 'user'
    if user_to_update:
        user_to_update.person_profile_id = None # Desvincular perfil de persona
        user_to_update.role = UserRole.CLIENT # O un rol por defecto
        db.add(user_to_update)
        db.commit()

    crud.teacher.remove(db, id=teacher_id)
    return {"message": "Perfil de profesor eliminado exitosamente."}