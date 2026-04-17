# backend/app/api/v1/api.py
from fastapi import APIRouter
from .endpoints import login, users, teachers, gym_classes, class_schedules, class_sessions, bookings, clients  

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(login.router, prefix="/login", tags=["Login"])
api_router.include_router(teachers.router, prefix="/teachers", tags=["Teachers"])
api_router.include_router(gym_classes.router, prefix="/gym-classes", tags=["Gym Classes"])
api_router.include_router(class_schedules.router, prefix="/class-schedules", tags=["class_schedules"]) # Nuevo
api_router.include_router(class_sessions.router, prefix="/class-sessions", tags=["class_sessions"])   # Nuevo
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])             # Nuevo
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])            