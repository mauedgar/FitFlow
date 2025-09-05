# backend/app/api/v1/api.py
from fastapi import APIRouter
from .endpoints import login, users, teachers, gym_classes

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(login.router, prefix="/login", tags=["Login"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["Teachers"])
api_router.include_router(gym_classes.router, prefix="/gym-classes", tags=["Gym Classes"])