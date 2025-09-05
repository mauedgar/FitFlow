import asyncio
from datetime import datetime, timedelta
import random
import uuid

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import get_password_hash
from app.models import User, Teacher, GymClass, Client, Membership # Asumiendo que Client hereda de Person
from app.models.user import UserRole
from app.models.gym_class import DifficultyLevel
from app.models.membership import MembershipPlan

# --- DATOS DE MUESTRA ---

# 3 INSTRUCTORES
TEACHERS_DATA = [
    {
        "user": {"email": "ana.perez@fitflow.com", "password": "password123", "role": UserRole.TRAINER},
        "profile": {"name": "Ana", "surname": "Pérez", "bio": "Instructora certificada de Yoga y Pilates con 5 años de experiencia.", "cuil": "27-12345678-5"}
    },
    {
        "user": {"email": "carlos.gomez@fitflow.com", "password": "password123", "role": UserRole.TRAINER},
        "profile": {"name": "Carlos", "surname": "Gómez", "bio": "Especialista en entrenamiento funcional y CrossFit Nivel 2.", "cuil": "20-87654321-8"}
    },
    {
        "user": {"email": "lucia.fernandez@fitflow.com", "password": "password123", "role": UserRole.TRAINER},
        "profile": {"name": "Lucía", "surname": "Fernández", "bio": "Apasionada por el baile y el fitness. Certificada en Zumba y ritmos latinos.", "cuil": "27-23456789-0"}
    }
]

# 5 CLIENTES
CLIENTS_DATA = [
    {"user": {"email": "juan.rodriguez@email.com", "password": "password123"}, "profile": {"name": "Juan", "surname": "Rodríguez"}},
    {"user": {"email": "maria.garcia@email.com", "password": "password123"}, "profile": {"name": "María", "surname": "García"}},
    {"user": {"email": "pedro.martinez@email.com", "password": "password123"}, "profile": {"name": "Pedro", "surname": "Martínez"}},
    {"user": {"email": "laura.sanchez@email.com", "password": "password123"}, "profile": {"name": "Laura", "surname": "Sánchez"}},
    {"user": {"email": "sofia.lopez@email.com", "password": "password123"}, "profile": {"name": "Sofía", "surname": "López"}},
]

# 10 CLASES POPULARES
CLASSES_DATA = [
    {"name": "CrossFit WOD", "description": "Entrenamiento del día de alta intensidad. Mejora tu fuerza y resistencia general.", "difficulty": DifficultyLevel.ADVANCED, "duration": 60},
    {"name": "BodyPump", "description": "Clase de entrenamiento con barra y discos que fortalece todo tu cuerpo.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 55},
    {"name": "Funcional", "description": "Entrenamiento basado en movimientos cotidianos para mejorar la agilidad y coordinación.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 50},
    {"name": "Yoga Vinyasa", "description": "Fluye a través de posturas de yoga sincronizadas con la respiración. Ideal para flexibilidad y calma.", "difficulty": DifficultyLevel.BEGINNER, "duration": 60},
    {"name": "Spinning", "description": "Clase de ciclismo indoor al ritmo de la música para un increíble desafío cardiovascular.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 45},
    {"name": "Zumba", "description": "¡La fiesta del fitness! Baila al ritmo de la música latina y quema calorías sin darte cuenta.", "difficulty": DifficultyLevel.BEGINNER, "duration": 50},
    {"name": "Boxeo Recreativo", "description": "Aprende las bases del boxeo, mejora tus reflejos y libera estrés en esta clase enérgica.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 60},
    {"name": "Pilates Mat", "description": "Fortalece tu core, mejora tu postura y alarga tus músculos con ejercicios en colchoneta.", "difficulty": DifficultyLevel.BEGINNER, "duration": 55},
    {"name": "Stronger", "description": "Desafía tus límites con un entrenamiento de fuerza pura enfocado en levantamiento pesado.", "difficulty": DifficultyLevel.ADVANCED, "duration": 75},
    {"name": "GAP (Glúteos, Abdomen, Piernas)", "description": "Clase localizada para tonificar y fortalecer el tren inferior y la zona media del cuerpo.", "difficulty": DifficultyLevel.INTERMEDIATE, "duration": 45},
]


async def seed_data(db: Session) -> None:
    print("Iniciando el sembrado de la base de datos...")

    # --- Crear Profesores y sus Usuarios asociados ---
    created_teachers = []
    for teacher_data in TEACHERS_DATA:
        user_info = teacher_data["user"]
        profile_info = teacher_data["profile"]

        user = db.query(User).filter(User.email == user_info["email"]).first()
        if not user:
            # Crear User
            user = User(
                email=user_info["email"],
                hashed_password=get_password_hash(user_info["password"]),
                role=user_info["role"],
            )
            # Crear Teacher (que también crea la entrada en Person)
            teacher = Teacher(
                **profile_info,
                user=user
            )
            db.add(teacher)
            created_teachers.append(teacher)
    
    # --- Crear Clientes y sus Usuarios asociados ---
    for client_data in CLIENTS_DATA:
        user_info = client_data["user"]
        profile_info = client_data["profile"]

        user = db.query(User).filter(User.email == user_info["email"]).first()
        if not user:
            # 1. Crear User
            user = User(
                email=user_info["email"],
                hashed_password=get_password_hash(user_info["password"]),
            )
            
            # 2. Crear el perfil Client
            client = Client(
                **profile_info,
                user=user
            )
            
            # 3. Crear su Membership asociada
            start_date = datetime.now()
            # Asignamos una membresía de 30 días por defecto
            end_date = start_date + timedelta(days=30)
            # Asignamos un plan aleatorio para tener variedad de datos
            random_plan = random.choice(list(MembershipPlan))

            client.membership = Membership(
                plan=random_plan,
                start_date=start_date,
                end_date=end_date,
                last_invoice_id=f"inv_{uuid.uuid4().hex[:8]}" # ID de factura de ejemplo
            )
            
            # Añadimos el cliente. SQLAlchemy, por la cascada, también añadirá el user y la membresía.
            db.add(client)

    db.commit()
    print(f"Creados {len(created_teachers)} profesores y {len(CLIENTS_DATA)} clientes.")

    # --- Crear Clases y asociarlas aleatoriamente a los profesores ---
    created_classes_count = 0
    if created_teachers:
        for class_data in CLASSES_DATA:
            class_exists = db.query(GymClass).filter(GymClass.name == class_data["name"]).first()
            if not class_exists:
                # Asignar 1 o 2 profesores aleatoriamente a cada clase
                num_teachers_for_class = random.randint(1, min(2, len(created_teachers)))
                assigned_teachers = random.sample(created_teachers, num_teachers_for_class)

                # Generar un horario aleatorio para la próxima semana
                random_day = random.randint(1, 7)
                random_hour = random.randint(8, 20)
                schedule_time = datetime.now() + timedelta(days=random_day)
                schedule_time = schedule_time.replace(hour=random_hour, minute=0, second=0, microsecond=0)

                new_class = GymClass(
                    name=class_data["name"],
                    description=class_data["description"],
                    difficulty=class_data["difficulty"],
                    duration_minutes=class_data["duration"],
                    schedule=schedule_time,
                    teachers=assigned_teachers
                )
                db.add(new_class)
                created_classes_count += 1
        db.commit()
    
    print(f"Creadas {created_classes_count} clases.")
    print("¡Sembrado de datos completado!")


async def main():
    db = SessionLocal()
    try:
        await seed_data(db)
    finally:
        db.close()

if __name__ == "__main__":
    # Esto permite ejecutar el script directamente desde la terminal
    print("Ejecutando seeder como un script independiente...")
    asyncio.run(main())