# backend/app/models/user.py

import uuid
from sqlalchemy import Column, DateTime, String, Boolean, Enum as SQLAlchemyEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TRAINER = "trainer"
    CLIENT = "client"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.CLIENT, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Opcional: Para Soft Deletes (borrado lógico)
    # En lugar de borrar la fila, marcarías esta fecha. Es más avanzado.
    # deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role}')>"

    