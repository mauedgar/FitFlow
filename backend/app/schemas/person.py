from pydantic import BaseModel
from typing import Optional

class PersonBase(BaseModel):
    first_name: str
    last_name: str
    passport: Optional[str] = None
    address: Optional[str] = None
    medical_fit_url: Optional[str] = None
    profile_image_url: Optional[str] = None

    # Todos los esquemas que lean de un modelo ORM necesitan esto
    class Config:
        from_attributes = True

class PersonCreate(PersonBase):
    pass

class PersonUpdate(PersonBase):
    pass