from urllib.parse import parse_qs, urlparse

import pytest
from faker import Faker
from httpx import AsyncClient

from app.models import Organization


@pytest.fixture
async def organization(faker: Faker) -> Organization:
    return await Organization.create(name=faker.company())


@pytest.fixture
async def authed_client(
    faker: Faker,
    client: AsyncClient,
    organization: Organization,
) -> AsyncClient:
    response = await client.get(
        "/authorize",
        params={"client_id": organization.id, "redirect_uri": faker.url()},
        follow_redirects=False,
    )
    assert response.status_code == 307

    location = response.headers["Location"]
    parsed = urlparse(location)
    qs = parse_qs(parsed.query)
    auth_code = qs["code"][0]

    response = await client.post(
        "/token",
        data={"grant_type": "authorization_code", "code": auth_code},
    )
    assert response.status_code == 200

    data = response.json()
    access_token = data["access_token"]

    client.headers["Authorization"] = f"Bearer {access_token}"
    return client
