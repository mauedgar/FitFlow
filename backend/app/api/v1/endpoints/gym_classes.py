from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=schemas.GymClass, status_code=status.HTTP_201_CREATED)
def create_gym_class(
    *,
    db: Session = Depends(get_db),
    class_in: schemas.GymClassCreate
):
    """
    Crea una nueva clase de gimnasio y la asocia con los profesores especificados.

    - **teacher_ids**: Una lista de UUIDs de los profesores que impartirán esta clase.
    """
    # 1. Llamamos a nuestro método CRUD especializado
    # Este método ya contiene toda la lógica de validación y asociación.
    new_class = crud.gym_class.create_with_teachers(db=db, obj_in=class_in)
    
    # 2. El CRUD devuelve None si algún ID de profesor no es válido.
    # El endpoint es responsable de traducir esto en una respuesta HTTP.
    if not new_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uno o más de los IDs de profesor proporcionados no existen.",
        )
        
    return new_class


@router.get("/", response_model=List[schemas.GymClass])
def read_gym_classes(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """
    Obtiene una lista de clases de gimnasio.
    El esquema de respuesta se encargará de incluir la lista de profesores.
    """
    gym_classes = crud.gym_class.get_multi(db, skip=skip, limit=limit)
    return gym_classes

@router.get("/{class_id}", response_model=schemas.GymClass)
def read_gym_class_by_id(
    *,
    db: Session = Depends(get_db),
    class_id: uuid.UUID
):
    """
    Obtiene los detalles de una clase de gimnasio específica por su ID.
    La respuesta incluirá la lista de profesores que imparten esta clase.
    """
    gym_class = crud.gym_class.get(db, id=class_id)
    if not gym_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La clase con id {class_id} no fue encontrada.",
        )
    return gym_class