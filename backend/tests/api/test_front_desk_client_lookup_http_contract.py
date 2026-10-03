"""HTTP contract for deterministic Front Desk Client lookup by document."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx
import pytest
from fastapi import status
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.db.models import Client, User
from app.db.session import AsyncSessionLocal, engine

pytestmark = [
    pytest.mark.api,
    pytest.mark.integration,
    pytest.mark.asyncio,
]


@dataclass(frozen=True)
class LookupFixture:
    document_number: str
    target_id: uuid.UUID
    neighbor_id: uuid.UUID
    target_email: str
    tokens: dict[UserRole, str]


@pytest.fixture(autouse=True)
def require_isolated_test_database() -> None:
    database_name = make_url(settings.DATABASE_URL).database
    assert database_name == "fitflow_test", (
        "Front Desk Client lookup contract requires fitflow_test; "
        f"configured database is {database_name!r}."
    )


@pytest.fixture(autouse=True)
async def dispose_engine_pool_after_test() -> AsyncIterator[None]:
    yield
    await engine.dispose()


async def _seed_lookup_fixture() -> LookupFixture:
    marker = uuid.uuid4().hex
    document_number = f"B2-{marker}"
    target_email = f"b2-target-{marker}@example.com"

    admin_user = User(
        email=f"b2-admin-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.admin,
    )
    front_desk_user = User(
        email=f"b2-front-desk-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.front_desk,
    )
    client_caller = User(
        email=f"b2-client-caller-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.client,
    )
    teacher_user = User(
        email=f"b2-teacher-{marker}@example.com",
        hashed_password="not-a-real-password",
        role=UserRole.teacher,
    )

    target = Client(
        first_name="Lookup",
        last_name="Target",
        document_number=document_number,
        user=User(
            email=target_email,
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )
    neighbor = Client(
        first_name="Lookup",
        last_name="Neighbor",
        document_number=f"{document_number}-EXTRA",
        user=User(
            email=f"b2-neighbor-{marker}@example.com",
            hashed_password="not-a-real-password",
            role=UserRole.client,
        ),
    )

    async with AsyncSessionLocal() as db:
        db.add_all([
            admin_user,
            front_desk_user,
            client_caller,
            teacher_user,
            target,
            neighbor,
        ])
        await db.flush()

        target_id = target.id
        neighbor_id = neighbor.id

        tokens = {
            UserRole.admin: create_access_token(
                {"sub": str(admin_user.id), "role": UserRole.admin.value}
            ),
            UserRole.front_desk: create_access_token(
                {"sub": str(front_desk_user.id), "role": UserRole.front_desk.value}
            ),
            UserRole.client: create_access_token(
                {"sub": str(client_caller.id), "role": UserRole.client.value}
            ),
            UserRole.teacher: create_access_token(
                {"sub": str(teacher_user.id), "role": UserRole.teacher.value}
            ),
        }
        await db.commit()

    return LookupFixture(
        document_number=document_number,
        target_id=target_id,
        neighbor_id=neighbor_id,
        target_email=target_email,
        tokens=tokens,
    )


@pytest.fixture
async def lookup_fixture() -> LookupFixture:
    return await _seed_lookup_fixture()


def _headers(fixture: LookupFixture, role: UserRole) -> dict[str, str]:
    return {"Authorization": f"Bearer {fixture.tokens[role]}"}


@pytest.mark.parametrize("role", [UserRole.admin, UserRole.front_desk])
async def test_lookup_allows_authorized_roles_and_resolves_exact_client(
    api_client: httpx.AsyncClient,
    lookup_fixture: LookupFixture,
    role: UserRole,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/clients/by-document",
        params={"document_number": lookup_fixture.document_number},
        headers=_headers(lookup_fixture, role),
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json() == {
        "id": str(lookup_fixture.target_id),
        "document_number": lookup_fixture.document_number,
        "full_name": "Lookup Target",
        "email": lookup_fixture.target_email,
    }


async def test_lookup_trims_outer_whitespace(
    api_client: httpx.AsyncClient,
    lookup_fixture: LookupFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/clients/by-document",
        params={"document_number": f"  {lookup_fixture.document_number}  "},
        headers=_headers(lookup_fixture, UserRole.front_desk),
    )

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["id"] == str(lookup_fixture.target_id)
    assert response.json()["document_number"] == lookup_fixture.document_number


async def test_lookup_unknown_document_is_not_found(
    api_client: httpx.AsyncClient,
    lookup_fixture: LookupFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/clients/by-document",
        params={"document_number": f"missing-{uuid.uuid4().hex}"},
        headers=_headers(lookup_fixture, UserRole.admin),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Cliente no encontrado."}


async def test_lookup_blank_document_is_rejected(
    api_client: httpx.AsyncClient,
    lookup_fixture: LookupFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/clients/by-document",
        params={"document_number": "   "},
        headers=_headers(lookup_fixture, UserRole.admin),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "El número de documento es obligatorio."}


async def test_lookup_does_not_partial_match(
    api_client: httpx.AsyncClient,
    lookup_fixture: LookupFixture,
) -> None:
    partial = lookup_fixture.document_number[:-1]
    response = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/clients/by-document",
        params={"document_number": partial},
        headers=_headers(lookup_fixture, UserRole.front_desk),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Cliente no encontrado."}
    assert lookup_fixture.target_id != lookup_fixture.neighbor_id


@pytest.mark.parametrize("role", [UserRole.client, UserRole.teacher])
async def test_lookup_rejects_unauthorized_roles(
    api_client: httpx.AsyncClient,
    lookup_fixture: LookupFixture,
    role: UserRole,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/clients/by-document",
        params={"document_number": lookup_fixture.document_number},
        headers=_headers(lookup_fixture, role),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {
        "detail": "Este recurso requiere uno de los siguientes roles: admin, front_desk."
    }


async def test_lookup_requires_authentication(
    api_client: httpx.AsyncClient,
    lookup_fixture: LookupFixture,
) -> None:
    response = await api_client.get(
        f"{settings.API_V1_STR}/front-desk/clients/by-document",
        params={"document_number": lookup_fixture.document_number},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}
    assert response.headers.get("www-authenticate") == "Bearer"
