from itertools import chain
from operator import attrgetter
from typing import Any

import pytest
from faker import Faker
from httpx import AsyncClient

from app.models import Organization
from tests.shorthands import any_str, uses_db


@pytest.fixture
async def organization(faker: Faker) -> Organization:
    return await Organization.create(name=faker.company())


@pytest.fixture
def serialized_organization(organization: Organization) -> dict[str, Any]:
    return {
        "id": organization.id,
        "create_time": any_str,
        "update_time": any_str,
        "name": organization.name,
    }


@uses_db
class TestListOrganizations:
    async def test_smoke(
        self,
        client: AsyncClient,
        organization: Organization,  # noqa: ARG002
        serialized_organization: dict[str, Any],
    ) -> None:
        response = await client.get("/organizations/")
        assert response.status_code == 200
        assert response.json() == {
            "items": [serialized_organization],
            "next_cursor": None,
        }


@uses_db
class TestGetOrganization:
    async def test_smoke(
        self,
        client: AsyncClient,
        organization: Organization,
        serialized_organization: dict[str, Any],
    ) -> None:
        response = await client.get(f"/organizations/{organization.id}")
        assert response.status_code == 200
        assert response.json() == serialized_organization


@uses_db
class TestPagination:
    url = "/organizations/"

    @pytest.fixture
    async def organizations(self, faker: Faker) -> list[Organization]:
        organizations = [
            await Organization.create(name=faker.company()) for _ in range(20)
        ]
        organizations.sort(key=attrgetter("id"), reverse=True)
        return organizations

    @pytest.mark.parametrize("per_page", [1, 3, 5, 9, 11, 50])
    async def test_all_pages(
        self,
        client: AsyncClient,
        organizations: list[Organization],
        per_page: int,
    ) -> None:
        pages: list[list[dict[str, Any]]] = []
        params = {"limit": per_page}
        while True:
            response = await client.get(self.url, params=params)
            assert response.status_code == 200
            data = response.json()

            pages.append(data["items"])

            next_cursor = data["next_cursor"]
            if not next_cursor:
                break
            params["cursor"] = next_cursor

        assert all(len(page) == per_page for page in pages[:-1])
        assert len(pages[-1]) <= per_page

        for obj, organization in zip(
            chain.from_iterable(pages),
            organizations,
            strict=True,
        ):
            assert obj["id"] == organization.id
            assert obj["name"] == organization.name

    @pytest.mark.parametrize("cursor", ["", "foobar", "1" * 1000])
    async def test_cursor_invalid(self, client: AsyncClient, cursor: str) -> None:
        response = await client.get(self.url, params={"cursor": cursor})
        assert response.status_code == 422

    @pytest.mark.parametrize("limit", ["", "foobar", "-1", "10000", "1" * 1000])
    async def test_limit_invalid(self, client: AsyncClient, limit: str) -> None:
        response = await client.get(self.url, params={"limit": limit})
        assert response.status_code == 422
