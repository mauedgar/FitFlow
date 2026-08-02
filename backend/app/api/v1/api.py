# backend/app/api/v1/api.py

from fastapi import APIRouter

from .endpoints import (
    login,
    users,
    teachers,
    clients,
    gym_classes,
    class_schedules,
    class_sessions,
    bookings,
    memberships,
)

api_router = APIRouter()

# -----------------------------
# Autenticación y Usuarios
# -----------------------------
api_router.include_router(login.router)
api_router.include_router(users.router)

# -----------------------------
# Perfiles (Person → Teacher / Client)
# -----------------------------
api_router.include_router(teachers.router)
api_router.include_router(clients.router)

# -----------------------------
# Dominio Principal del Gimnasio
# -----------------------------
api_router.include_router(gym_classes.router)
api_router.include_router(class_schedules.router)
api_router.include_router(class_sessions.router)
api_router.include_router(bookings.router)
api_router.include_router(memberships.router)
