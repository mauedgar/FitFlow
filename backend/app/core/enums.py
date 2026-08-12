# app/schemas/enums.py
from enum import StrEnum


class UserRole(StrEnum):
    """Roles de acceso disponibles dentro del sistema.

    - admin: acceso completo al panel operativo y de administración.
    - teacher: acceso a sesiones asignadas y gestión de asistencia.
    - client: acceso al dashboard personal, agenda y reservas.
    - front_desk:
    """

    admin = "admin"
    teacher = "teacher"
    client = "client"
    front_desk = "front_desk"

class DifficultyLevel(StrEnum):
    """Niveles de dificultad disponibles para una actividad del catálogo.

    Se utilizan valores estables en lowercase para mantener consistencia
    entre el backend, la base de datos y la API. La traducción a etiquetas
    amigables puede resolverse en el frontend.
    """

    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class BookingStatus(StrEnum):
    """Estados posibles de una reserva.

    - confirmed: la reserva fue creada correctamente y el cupo quedó tomado.
    - cancelled: la reserva fue cancelada por el cliente o por el staff.
    - attended: el cliente realizó check-in y asistió efectivamente.
    - no_show: el cliente tenía reserva, pero no asistió.
    """

    confirmed = "confirmed"
    cancelled = "cancelled"
    attended = "attended"
    no_show = "no_show"

class MembershipPlan(StrEnum):
    """Tipos de membresía que ofrece el gimnasio.

    - gym_only: acceso a musculación o gimnasio libre.
    - classes: acceso a clases grupales.
    - premium: acceso combinado a musculación y clases.
    - personalized: acceso premium más atención o entrenamiento personalizado.
    """

    gym_only = "gym_only"
    classes = "classes"
    premium = "premium"
    personalized = "personalized"

class MembershipStatus(StrEnum):
    """Estados operativos posibles de una membresía.

    - active: la membresía está vigente y habilitada.
    - expired: la vigencia terminó.
    - paused: la membresía está temporalmente suspendida.
    - cancelled: la membresía fue dada de baja.
    """

    active = "active"
    expired = "expired"
    paused = "paused"
    cancelled = "cancelled"

class ActivityType(StrEnum):
    """Tipos de actividad que el gimnasio puede ofrecer dentro del catálogo.

    - group_class: clases grupales tradicionales.
    - open_gym: franjas de musculación o uso libre del gimnasio.
    - personal_training: sesiones individuales o personalizadas.
    """

    group_class = "group_class"
    open_gym = "open_gym"
    personal_training = "personal_training"

class AllowedPlan(StrEnum):
    """Planes de membresía habilitados para una oferta recurrente.

    Este enum permite restringir qué tipo de cliente puede reservar
    las sesiones generadas a partir de este horario.
    """

    classes = "classes"
    premium = "premium"
    personalized = "personalized"

class ClassSessionStatus(StrEnum):
    """Estados posibles de una sesión concreta.

    - scheduled: la sesión está programada y disponible para operar.
    - cancelled: la sesión fue cancelada y no debe aceptar reservas nuevas.
    - completed: la sesión ya finalizó su ejecución operativa.
    """

    draft = "draft"
    scheduled = "scheduled"
    open = "open"
    closed = "closed"
    cancelled = "cancelled"
    completed = "completed"

