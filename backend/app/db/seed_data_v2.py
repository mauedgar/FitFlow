# seed_data_v2.py
import asyncio
from datetime import datetime, timedelta, time, date
import random
import uuid

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models import (
    User, Teacher, GymClass, Client, Membership,
    ClassSchedule, ClassSession  # Nuevos modelos
)
from app.models.user import UserRole
from app.models.gym_class import DifficultyLevel
from app.models.membership import MembershipPlan


# --- DATOS ACTUALIZADOS ---

TEACHERS_DATA = [
    {
        "user": {"email": "ana.perez@fitflow.com", "password": "password123", "role": UserRole.TRAINER},
        "profile": {"name": "Ana", "last_name": "Pérez", "bio": "Instructora certificada de Yoga y Pilates con 5 años de experiencia.", "cuil": "27-12345678-5"}
    },
    {
        "user": {"email": "carlos.gomez@fitflow.com", "password": "password123", "role": UserRole.TRAINER},
        "profile": {"name": "Carlos", "last_name": "Gómez", "bio": "Especialista en entrenamiento funcional y CrossFit Nivel 2.", "cuil": "20-87654321-8"}
    },
    {
        "user": {"email": "lucia.fernandez@fitflow.com", "password": "password123", "role": UserRole.TRAINER},
        "profile": {"name": "Lucía", "last_name": "Fernández", "bio": "Apasionada por el baile y el fitness. Certificada en Zumba y ritmos latinos.", "cuil": "27-23456789-0"}
    }
]

CLIENTS_DATA = [
    {"user": {"email": "juan.rodriguez@email.com", "password": "password123"}, "profile": {"name": "Juan", "last_name": "Rodríguez"}},
    {"user": {"email": "maria.garcia@email.com", "password": "password123"}, "profile": {"name": "María", "last_name": "García"}},
    {"user": {"email": "pedro.martinez@email.com", "password": "password123"}, "profile": {"name": "Pedro", "last_name": "Martínez"}},
    {"user": {"email": "laura.sanchez@email.com", "password": "password123"}, "profile": {"name": "Laura", "last_name": "Sánchez"}},
    {"user": {"email": "sofia.lopez@email.com", "password": "password123"}, "profile": {"name": "Sofía", "last_name": "López"}},
]

# CLASES CON DEFAULT_CAPACITY ACTUALIZADO
CLASSES_DATA = [
    {"name": "CrossFit WOD", "description": "Entrenamiento del día de alta intensidad.", "difficulty": DifficultyLevel.ADVANCED, "duration": 60, "default_capacity": 15},
    {"name": "BodyPump", "description": "Clase de entrenamiento con barra y discos.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 55, "default_capacity": 20},
    {"name": "Funcional", "description": "Entrenamiento basado en movimientos cotidianos.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 50, "default_capacity": 18},
    {"name": "Yoga Vinyasa", "description": "Fluye a través de posturas de yoga.", "difficulty": DifficultyLevel.BEGINNER, "duration": 60, "default_capacity": 25},
    {"name": "Spinning", "description": "Clase de ciclismo indoor al ritmo de la música.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 45, "default_capacity": 30},
    {"name": "Zumba", "description": "¡La fiesta del fitness! Baila al ritmo de la música latina.", "difficulty": DifficultyLevel.BEGINNER, "duration": 50, "default_capacity": 35},
    {"name": "Boxeo Recreativo", "description": "Aprende las bases del boxeo.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 60, "default_capacity": 12},
    {"name": "Pilates Mat", "description": "Fortalece tu core, mejora tu postura.", "difficulty": DifficultyLevel.BEGINNER, "duration": 55, "default_capacity": 20},
    {"name": "Stronger", "description": "Desafía tus límites con entrenamiento de fuerza.", "difficulty": DifficultyLevel.ADVANCED, "duration": 75, "default_capacity": 10},
    {"name": "GAP", "description": "Glúteos, Abdomen y Piernas.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 45, "default_capacity": 25},
]

# HORARIOS TÍPICOS DE GIMNASIO
SCHEDULE_TEMPLATES = [
    {"days": [0, 2, 4], "time": "07:00"},  # Lunes, Miércoles, Viernes temprano
    {"days": [0, 2, 4], "time": "09:00"},  # Lunes, Miércoles, Viernes mañana
    {"days": [1, 3], "time": "18:00"},     # Martes, Jueves tarde
    {"days": [1, 3], "time": "19:30"},     # Martes, Jueves noche
    {"days": [5], "time": "10:00"},        # Sábado mañana
]

async def seed_data(db: Session) -> None:
    print("🌱 Iniciando el sembrado de la base de datos v2...")

    # --- 1. CREAR PROFESORES ---
    created_teachers = []
    for teacher_data in TEACHERS_DATA:
        user_info = teacher_data["user"]
        profile_info = teacher_data["profile"]

        user = db.query(User).filter(User.email == user_info["email"]).first()
        if not user:
            user = User(
                email=user_info["email"],
                hashed_password=get_password_hash(user_info["password"]),
                role=user_info["role"],
            )
            teacher = Teacher(**profile_info, user=user)
            db.add(teacher)
            created_teachers.append(teacher)
        else:
            # Busca el Teacher asociado al usuario existente
            teacher = db.query(Teacher).filter(Teacher.user_id == user.id).first()
            if teacher:
                created_teachers.append(teacher)
    
    # --- 2. CREAR CLIENTES ---
    for client_data in CLIENTS_DATA:
        user_info = client_data["user"]
        profile_info = client_data["profile"]

        user = db.query(User).filter(User.email == user_info["email"]).first()
        if not user:
            user = User(
                email=user_info["email"],
                hashed_password=get_password_hash(user_info["password"]),
                role=UserRole.CLIENT,
            )
            
            client = Client(**profile_info, user=user)
            
            # Crear membresía
            start_date = datetime.now()
            end_date = start_date + timedelta(days=30)
            random_plan = random.choice(list(MembershipPlan))

            client.membership = Membership(
                plan=random_plan,
                start_date=start_date,
                end_date=end_date,
                last_invoice_id=f"inv_{uuid.uuid4().hex[:8]}"
            )
            
            db.add(client)

    db.commit()
    print(f"✅ Creados {len(created_teachers)} profesores y {len(CLIENTS_DATA)} clientes")

    # --- 3. CREAR CLASES CON DEFAULT_CAPACITY ---
    created_classes = []
    for class_data in CLASSES_DATA:
        class_exists = db.query(GymClass).filter(GymClass.name == class_data["name"]).first()
        if not class_exists:
            new_class = GymClass(
                name=class_data["name"],
                description=class_data["description"],
                difficulty=class_data["difficulty"],
                duration_minutes=class_data["duration"],
                default_capacity=class_data["default_capacity"]  # NUEVO CAMPO
            )
            db.add(new_class)
            created_classes.append(new_class)
        else:
            # Busca la gym-class asociada a la existente
            clas = db.query(GymClass).filter(GymClass.name == class_data["name"]).first()
            if clas:
                created_classes.append(clas)
    
    db.commit()
    print(f"✅ Creadas {len(created_classes)} clases")

    # --- 4. CREAR CLASS SCHEDULES (HORARIOS RECURRENTES) ---
    schedules_created = 0
    for gym_class in created_classes:
        # Asignar 1-2 horarios por clase
        num_schedules = random.randint(1, 2)
        
        for _ in range(num_schedules):
            schedule_template = random.choice(SCHEDULE_TEMPLATES)
            teacher = random.choice(created_teachers)
            
            # Parsear hora
            hour, minute = map(int, schedule_template["time"].split(":"))
            
            class_schedule = ClassSchedule(
                gym_class_id=gym_class.id,
                teacher_id=teacher.id,
                days_of_week=schedule_template["days"],
                start_time=time(hour, minute),
                duration_minutes=time(hour + 1, minute),  # Duración de 1 hora
                capacity=gym_class.default_capacity,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=90)  # 3 meses
            )
            db.add(class_schedule)
            schedules_created += 1
    
    db.commit()
    print(f"✅ Creados {schedules_created} horarios de clases")

    # --- 5. GENERAR CLASS SESSIONS PARA LA PRÓXIMA SEMANA ---
    sessions_created = 0
    all_schedules = db.query(ClassSchedule).all()
    
    for schedule in all_schedules:
        # Generar sesiones para los próximos 7 días
        for day_offset in range(7):
            check_date = date.today() + timedelta(days=day_offset)
            weekday = check_date.weekday()
            
            # Si este día coincide con el horario
            if weekday in schedule.days_of_week:
                session_start = datetime.combine(check_date, schedule.start_time)
                session_end = datetime.combine(check_date, schedule.duration_minutes)
                
                class_session = ClassSession(
                    class_schedule_id=schedule.id,
                    starts_at=session_start,
                    ends_at=session_end,
                    status=False
                )
                db.add(class_session)
                sessions_created += 1
    
    db.commit()
    print(f"✅ Creadas {sessions_created} sesiones de clases para la próxima semana")

        # --- 5. GENERAR CLASS SESSIONS PARA LAS PRÓXIMAS 4 SEMANAS ---
    def generate_sessions_for_schedule(db: Session, schedule: ClassSchedule, weeks: int = 4):
        """Genera sesiones específicas para un horario recurrente"""
        sessions_created = 0
        
        for week in range(weeks):
            for day_of_week in schedule.days_of_week:
                # Calcular la fecha de la próxima ocurrencia
                days_ahead = day_of_week - date.today().weekday()
                if days_ahead <= 0:  # Si ya pasó esta semana
                    days_ahead += 7
                
                # Agregar las semanas correspondientes
                days_ahead += (week * 7)
                session_date = date.today() + timedelta(days=days_ahead)
                
                # Combinar fecha con hora
                starts_at = datetime.combine(session_date, schedule.start_time)
                ends_at = datetime.combine(session_date, schedule.duration_minutes)
                
                # Crear la sesión si está dentro del rango del schedule
                if schedule.start_date <= session_date <= (schedule.end_date or session_date):
                    session = ClassSession(
                        class_schedule_id=schedule.id,
                        starts_at=starts_at,
                        ends_at=ends_at,
                        status=False
                    )
                    db.add(session)
                    sessions_created += 1
        
        return sessions_created

    # En tu función seed_data, después de crear los ClassSchedule:
    print("Generando sesiones de clases...")
    total_sessions = 0
    all_schedules = db.query(ClassSchedule).all()
    for schedule in all_schedules:
        sessions = generate_sessions_for_schedule(db, schedule, weeks=4)
        total_sessions += sessions

    db.commit()
    print(f"✅ Creadas {total_sessions} sesiones de clases")
    
    print("🎉 ¡Sembrado de datos v2 completado!")


async def main():
    db = SessionLocal()
    try:
        await seed_data(db)
    finally:
        db.close()

if __name__ == "__main__":
    print("Ejecutando seeder v2...")
    asyncio.run(main())