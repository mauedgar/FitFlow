from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db.session import get_db
# from app.api.deps import get_current_active_user # Futura mejora de seguridad

router = APIRouter()
# Este endpoint asume que un 'User' ya existe y le vamos a crear
# su perfil de 'Teacher' (que hereda de 'Person').
@router.post("/{user_id}", response_model=schemas.Teacher, status_code=status.HTTP_201_CREATED)
def create_teacher_for_user(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    teacher_in: schemas.TeacherCreate
):
    """
    Crea un perfil de profesor para un usuario existente.
    En un futuro, esto debería ser una ruta protegida para administradores.
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

    # 3. Usar el CRUD para crear el perfil de profesor y asociarlo
    teacher = crud.teacher.create_with_user(db=db, obj_in=teacher_in, user=user)
    
    return teacher

@router.get("/", response_model=List[schemas.Teacher])
def read_teachers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Obtiene una lista de profesores.
    """
    teachers = crud.teacher.get_multi(db, skip=skip, limit=limit)
    return teachers

@router.get("/{teacher_id}", response_model=schemas.Teacher)
def read_teacher_by_id(
    *,
    db: Session = Depends(get_db),
    teacher_id: uuid.UUID
):
    """
    Obtiene los detalles de un profesor específico por su ID.
    """
    teacher = crud.teacher.get(db, id=teacher_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El profesor con id {teacher_id} no fue encontrado.",
        )
    return teacher
