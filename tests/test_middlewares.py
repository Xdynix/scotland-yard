from httpx import AsyncClient
from pytest_mock import MockerFixture

from app import settings


async def test_random_error(mocker: MockerFixture, client: AsyncClient) -> None:
    mocker.patch.object(settings, "RANDOM_ERROR_RATE", 1)
    response = await client.get("/")
    assert response.status_code == 500
    assert response.json() == "This is a simulated error. Please try again."
