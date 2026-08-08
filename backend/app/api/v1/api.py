# backend/app/api/v1/api.py

from fastapi import APIRouter

from app.routers import (
    auth,
    bookings,
    class_schedules,
    class_sessions,
    clients,
    front_desk,
    gym_classes,
    memberships,
    teachers,
    users,
)

api_router = APIRouter()

# -----------------------------
# Autenticación y Usuarios
# -----------------------------
api_router.include_router(auth.router)
api_router.include_router(users.router)

# -----------------------------
# Perfiles (Person → Teacher / Client / front_desk)
# -----------------------------
api_router.include_router(teachers.router)
api_router.include_router(clients.router)
api_router.include_router(front_desk.router)
# -----------------------------
# Dominio Principal del Gimnasio
# -----------------------------
api_router.include_router(gym_classes.router)
api_router.include_router(class_schedules.router)
api_router.include_router(class_sessions.router)
api_router.include_router(bookings.router)
api_router.include_router(memberships.router)
