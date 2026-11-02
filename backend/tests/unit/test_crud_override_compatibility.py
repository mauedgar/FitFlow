"""Contract regressions for specialized CRUDBase overrides.

All fixtures are synthetic and no database connection or SQL effect occurs.
"""

from inspect import signature
from uuid import uuid4

import pytest
from app.crud.base import CRUDBase
from app.crud.crud_booking import CRUDBooking
from app.crud.crud_class_schedule import CRUDClassSchedule
from app.crud.crud_class_session import CRUDClassSession
from app.crud.crud_gym_class import CRUDGymClass
from app.crud.crud_membership import CRUDMembership
from app.crud.crud_teacher import CRUDTeacher
from app.crud.crud_user import CRUDUser
from app.db.models import ClassSchedule, GymClass, User
from app.services.errors import BusinessValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import raiseload
from sqlalchemy.orm.interfaces import ORMOption


@pytest.mark.parametrize(
    "crud_class",
    (
        CRUDBooking,
        CRUDClassSchedule,
        CRUDClassSession,
        CRUDGymClass,
        CRUDMembership,
        CRUDTeacher,
        CRUDUser,
    ),
)
def test_specialized_get_accepts_base_keywords(crud_class):
    base = signature(CRUDBase.get)
    specialized = signature(crud_class.get)
    assert all(name in specialized.parameters for name in base.parameters)


@pytest.mark.asyncio
async def test_specialized_get_merges_requested_loader_options(monkeypatch):
    observed = {}

    async def fake_base_get(self, db, *, obj_id, options=None):
        observed["options"] = options

    monkeypatch.setattr(CRUDBase, "get", fake_base_get)
    extra_options: list[ORMOption] = [raiseload("*")]
    async with AsyncSession() as db:
        result = await CRUDGymClass(GymClass).get(
            db, obj_id=uuid4(), include_schedules=True, options=extra_options
        )
    assert result is None
    assert len(observed["options"]) == len(extra_options) + 1


@pytest.mark.asyncio
async def test_user_update_dict_hashes_password_before_base_update(monkeypatch):
    observed = {}

    async def fake_base_update(self, db, *, db_obj, obj_in):
        observed.update(obj_in)
        return db_obj

    monkeypatch.setattr(CRUDBase, "update", fake_base_update)
    monkeypatch.setattr(
        "app.crud.crud_user.get_password_hash", lambda password: "hashed:" + password
    )
    async with AsyncSession() as db:
        subject = User()
        result = await CRUDUser(User).update(
            db, db_obj=subject, obj_in={"password": "synthetic-secret"}
        )
    assert result is subject
    assert observed["hashed_password"] == "hashed:synthetic-secret"
    assert "password" not in observed


@pytest.mark.asyncio
async def test_user_update_rejects_nonstring_password(monkeypatch):
    async with AsyncSession() as db:
        with pytest.raises(TypeError, match="Password must be a string"):
            await CRUDUser(User).update(
                db, db_obj=User(), obj_in={"password": object()}
            )


@pytest.mark.asyncio
async def test_schedule_update_rejects_negative_capacity_from_dict():
    async with AsyncSession() as db:
        with pytest.raises(BusinessValidationError, match="Capacity"):
            await CRUDClassSchedule(ClassSchedule).update(
                db, db_obj=ClassSchedule(), obj_in={"capacity": -1}
            )


@pytest.mark.asyncio
async def test_schedule_remove_preserves_id_and_object_contracts(monkeypatch):
    schedule = ClassSchedule()
    observed = []

    async def fake_get(self, db, *, obj_id, **kwargs):
        return schedule

    async def fake_base_remove(self, db, *, db_obj, hard=False):
        observed.append((db_obj, hard))

    monkeypatch.setattr(CRUDClassSchedule, "get", fake_get)
    monkeypatch.setattr(CRUDBase, "remove", fake_base_remove)
    async with AsyncSession() as db:
        crud = CRUDClassSchedule(ClassSchedule)
        await crud.remove(db, obj_id=uuid4())
        await crud.remove(db, db_obj=schedule, hard=True)
        with pytest.raises(ValueError, match="not both"):
            await crud.remove(db, db_obj=schedule, obj_id=uuid4())
        with pytest.raises(ValueError, match="Hard delete requires"):
            await crud.remove(db, obj_id=uuid4(), hard=True)
    assert observed == [(schedule, False), (schedule, True)]
