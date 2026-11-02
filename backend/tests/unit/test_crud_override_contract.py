"""Contract regressions for typed CRUD overrides and SQL row locking.

No persistent database, secrets, or external services are required.
"""

from inspect import Parameter, signature

import pytest
from app.crud.crud_booking import booking
from app.crud.crud_class_schedule import class_schedule
from app.crud.crud_class_session import class_session
from app.crud.crud_gym_class import gym_class
from app.crud.crud_membership import membership
from app.crud.crud_teacher import teacher
from app.crud.crud_user import user
from app.db.models import Client, Person, User
from sqlalchemy import select
from sqlalchemy.dialects import postgresql


@pytest.mark.parametrize(
    "crud",
    (booking, class_schedule, class_session, gym_class, membership, teacher, user),
)
def test_specialized_get_preserves_generic_options_contract(crud) -> None:
    parameters = signature(type(crud).get).parameters
    assert parameters["obj_id"].kind is Parameter.KEYWORD_ONLY
    assert parameters["options"].kind is Parameter.KEYWORD_ONLY
    assert parameters["options"].default is None


def test_schedule_remove_supports_both_existing_and_generic_signatures() -> None:
    parameters = signature(type(class_schedule).remove).parameters
    assert {"db_obj", "hard", "obj_id"} <= set(parameters)
    assert parameters["db_obj"].default is None
    assert parameters["hard"].default is False
    assert parameters["obj_id"].default is None


def test_client_row_lock_targets_preserve_postgres_table_names() -> None:
    statement = select(Client).join(Client.user).with_for_update(
        of=(User.id, Person.id, Client.id),
    )
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert sql.endswith("FOR UPDATE OF users, persons, clients")


def test_sqlalchemy_mapper_args_remain_runtime_dicts() -> None:
    for model, identity in ((Person, "person"), (Client, "client")):
        assert isinstance(model.__mapper_args__, dict)
        assert model.__mapper_args__["polymorphic_identity"] == identity
