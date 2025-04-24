from typing import Any, Protocol
from urllib.parse import parse_qs, urlencode, urlparse

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app import settings
from app.main import app
from tests.shorthands import any_number, any_str

client = TestClient(app)

authorization_url = "/authorize"
token_url = "/token"
me_url = "/me"


@pytest.fixture
def client_id(faker: Faker) -> str:
    return str(faker.random_int(1, 1000000))


class AuthCodeFactory(Protocol):
    def __call__(self, expired: bool = False) -> str: ...


@pytest.fixture
def get_auth_code(
    mocker: MockerFixture,
    faker: Faker,
    client_id: str,
) -> AuthCodeFactory:
    def _get_auth_code(expired: bool = False) -> str:
        if expired:
            mocker.patch.object(settings.AUTH, "auth_code_expire_minutes", -1)

        response = client.get(
            authorization_url,
            params={"client_id": client_id, "redirect_uri": faker.url(), "state": ""},
            follow_redirects=False,
        )
        assert response.status_code == 307

        location = response.headers["Location"]
        parsed = urlparse(location)
        qs = parse_qs(parsed.query)
        return qs["code"][0]

    return _get_auth_code


class TokenCredentialsFactory(Protocol):
    def __call__(self, expired: bool = False) -> tuple[str, str]: ...


@pytest.fixture
def get_token_credentials(
    mocker: MockerFixture,
    get_auth_code: AuthCodeFactory,
) -> TokenCredentialsFactory:
    auth_code = get_auth_code()

    def _get_token_credentials(expired: bool = False) -> tuple[str, str]:
        if expired:
            mocker.patch.object(settings.AUTH, "access_token_expire_minutes", -1)
            mocker.patch.object(settings.AUTH, "refresh_token_expire_minutes", -1)

        response = client.post(
            token_url,
            data={"grant_type": "authorization_code", "code": auth_code},
        )
        assert response.status_code == 200

        data = response.json()
        return data["access_token"], data["refresh_token"]

    return _get_token_credentials


class TestAuthorize:
    def test_smoke(self, faker: Faker, client_id: str) -> None:
        redirect_uri = f"{faker.url()}{faker.uri_path()}"
        state = faker.uuid4()

        response = client.get(
            authorization_url,
            params={
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "state": state,
            },
            follow_redirects=False,
        )
        assert response.status_code == 307

        location = response.headers["Location"]
        parsed = urlparse(location)
        qs = parse_qs(parsed.query)

        assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == redirect_uri
        assert qs["code"] == [any_str]
        assert qs["state"] == [state]

        auth_code = qs["code"][0]
        response = client.post(
            token_url,
            data={"grant_type": "authorization_code", "code": auth_code},
        )
        assert response.status_code == 200

    def test_redirect_uri_with_query(self, faker: Faker, client_id: str) -> None:
        params = {
            "foo": faker.uuid4(),
            "bar": faker.uuid4(),
        }
        redirect_uri = f"{faker.url()}{faker.uri_path()}?{urlencode(params)}"

        response = client.get(
            authorization_url,
            params={
                "client_id": client_id,
                "redirect_uri": redirect_uri,
            },
            follow_redirects=False,
        )
        assert response.status_code == 307

        location = response.headers["Location"]
        parsed = urlparse(location)
        qs = parse_qs(parsed.query)

        assert qs["code"] == [any_str]
        for key, value in params.items():
            assert qs[key] == [value]


class TestToken:
    def test_authorization_code_flow(self, get_auth_code: AuthCodeFactory) -> None:
        auth_code = get_auth_code()
        response = client.post(
            token_url,
            data={"grant_type": "authorization_code", "code": auth_code},
        )
        assert response.status_code == 200

        data = response.json()
        self.assert_token_response_is_valid(data)

    def test_authorization_code_flow_expired(
        self,
        get_auth_code: AuthCodeFactory,
    ) -> None:
        auth_code = get_auth_code(expired=True)
        response = client.post(
            token_url,
            data={"grant_type": "authorization_code", "code": auth_code},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_grant"

    @pytest.mark.parametrize("token", ["", "invalid", "1" * 1024])
    def test_authorization_code_flow_invalid(self, token: str) -> None:
        response = client.post(
            token_url,
            data={"grant_type": "authorization_code", "code": token},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_grant"

    def test_refresh_token_flow(
        self,
        get_token_credentials: TokenCredentialsFactory,
    ) -> None:
        old_access_token, old_refresh_token = get_token_credentials()

        response = client.post(
            token_url,
            data={"grant_type": "refresh_token", "refresh_token": old_refresh_token},
        )
        assert response.status_code == 200

        data = response.json()
        self.assert_token_response_is_valid(data)

        new_access_token = data["access_token"]
        new_refresh_token = data["refresh_token"]
        assert new_access_token != old_access_token
        assert new_refresh_token == old_refresh_token

    def test_refresh_token_flow_expired(
        self,
        get_token_credentials: TokenCredentialsFactory,
    ) -> None:
        _, refresh_token = get_token_credentials(expired=True)
        response = client.post(
            token_url,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_grant"

    @pytest.mark.parametrize("token", ["", "invalid", "1" * 1024])
    def test_refresh_token_flow_invalid(self, token: str) -> None:
        response = client.post(
            token_url,
            data={"grant_type": "refresh_token", "refresh_token": token},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_grant"

    def test_refresh_token_flow_incorrect_token_type(
        self,
        get_auth_code: AuthCodeFactory,
    ) -> None:
        token = get_auth_code()
        response = client.post(
            token_url,
            data={"grant_type": "refresh_token", "refresh_token": token},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_grant"

    def test_invalid_grant_type(self) -> None:
        response = client.post(
            token_url,
            data={"grant_type": "invalid", "foo": "bar"},
        )
        assert response.status_code == 400
        assert response.json()["error"] == "unsupported_grant_type"

    @classmethod
    def assert_token_response_is_valid(cls, data: dict[str, Any]) -> None:
        assert data == {
            "access_token": any_str,
            "refresh_token": any_str,
            "expires_in": any_number,
            "token_type": "bearer",
        }

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        cls.assert_access_token_is_valid(access_token)
        cls.assert_refresh_token_is_valid(refresh_token)

    @classmethod
    def assert_access_token_is_valid(cls, access_token: str) -> None:
        response = client.get(
            me_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200

    @classmethod
    def assert_refresh_token_is_valid(cls, refresh_token: str) -> None:
        response = client.post(
            token_url,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        assert response.status_code == 200


class TestGetMe:
    def test_smoke(
        self,
        client_id: str,
        get_token_credentials: TokenCredentialsFactory,
    ) -> None:
        access_token, _ = get_token_credentials()
        response = client.get(
            me_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        assert response.json() == {"organization_id": int(client_id)}

    def test_expired(self, get_token_credentials: TokenCredentialsFactory) -> None:
        access_token, _ = get_token_credentials(expired=True)
        response = client.get(
            me_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 401

    @pytest.mark.parametrize("token", ["", "invalid", "1" * 1024])
    def test_invalid(self, token: str) -> None:
        response = client.get(
            me_url,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
