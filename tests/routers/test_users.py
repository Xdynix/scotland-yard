from typing import Any

import pytest
from faker import Faker
from httpx import AsyncClient

from app.models import Organization, User
from tests.shorthands import any_str, uses_db


@pytest.fixture
async def user(faker: Faker, organization: Organization) -> User:
    return await User.create(
        organization=organization,
        username=faker.user_name(),
        email=faker.email(),
        active=faker.boolean(),
        role=faker.random_element(User.Role),
        first_name=faker.first_name(),
        last_name=faker.last_name(),
    )


@pytest.fixture
async def user_other_org(faker: Faker) -> User:
    other_org = await Organization.create(name=faker.company())
    return await User.create(
        organization=other_org,
        username=faker.user_name(),
        email=faker.email(),
    )


@pytest.fixture
def serialized_user(organization: Organization, user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "create_time": any_str,
        "update_time": any_str,
        "organization_id": organization.id,
        "username": user.username,
        "email": user.email,
        "active": user.active,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@uses_db
class TestListUsers:
    async def test_smoke(
        self,
        authed_client: AsyncClient,
        user: User,  # noqa: ARG002
        user_other_org: User,  # noqa: ARG002
        serialized_user: dict[str, Any],
    ) -> None:
        response = await authed_client.get("/users/")
        assert response.status_code == 200
        assert response.json() == {
            "items": [serialized_user],
            "next_cursor": None,
        }


@uses_db
class TestGetUser:
    async def test_smoke(
        self,
        authed_client: AsyncClient,
        user: User,
        serialized_user: dict[str, Any],
    ) -> None:
        response = await authed_client.get(f"/users/{user.id}")
        assert response.status_code == 200
        assert response.json() == serialized_user

    async def test_other_org(
        self,
        authed_client: AsyncClient,
        user_other_org: User,
    ) -> None:
        response = await authed_client.get(f"/users/{user_other_org.id}")
        assert response.status_code == 404

    async def test_not_found(self, authed_client: AsyncClient) -> None:
        response = await authed_client.get("/users/1")
        assert response.status_code == 404
