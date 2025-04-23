from faker import Faker
from httpx import AsyncClient

from app.models import Organization
from tests.shorthands import any_number, any_str, uses_db


@uses_db
class TestListOrganizations:
    async def test_smoke(self, faker: Faker, client: AsyncClient) -> None:
        name = faker.company()
        await Organization.create(name=name)

        response = await client.get("/organizations/")
        assert response.status_code == 200
        assert response.json() == {
            "items": [
                {
                    "id": any_number,
                    "create_time": any_str,
                    "update_time": any_str,
                    "name": name,
                }
            ],
            "next_cursor": None,
        }
