from httpx import AsyncClient

from tests.shorthands import approx_now


async def test_ping(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == approx_now()
