from typing import Any

import pytest
from faker import Faker
from httpx import AsyncClient

from app.models import Item, Organization, SharingLink, User
from tests.shorthands import any_str, uses_db


@pytest.fixture
async def user(faker: Faker, organization: Organization) -> User:
    return await User.create(
        organization=organization,
        username=faker.user_name(),
        email=faker.email(),
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
async def folder(faker: Faker, user: User) -> Item:
    return await Item.create(
        owner=user,
        parent=None,
        name=faker.word(),
        type=Item.Type.FOLDER,
    )


@pytest.fixture
async def folder_other_org(faker: Faker, user_other_org: User) -> Item:
    return await Item.create(
        owner=user_other_org,
        parent=None,
        name=faker.word(),
        type=Item.Type.FOLDER,
    )


@pytest.fixture
async def folder_other_user(faker: Faker, organization: Organization) -> Item:
    other_user = await User.create(
        organization=organization,
        username=faker.user_name(),
        email=faker.email(),
    )
    return await Item.create(
        owner=other_user,
        parent=None,
        name=faker.word(),
        type=Item.Type.FOLDER,
    )


@pytest.fixture
async def file(faker: Faker, user: User, folder: Item) -> Item:
    return await Item.create(
        owner=user,
        parent=folder,
        name=faker.file_name(),
        type=Item.Type.FILE,
        file_size=faker.random_int(1, 2**30),
    )


@pytest.fixture
async def file_other_org(faker: Faker, user_other_org: User) -> Item:
    return await Item.create(
        owner=user_other_org,
        parent=None,
        name=faker.file_name(),
        type=Item.Type.FILE,
        file_size=faker.random_int(1, 2**30),
    )


@pytest.fixture
async def file_other_folder(faker: Faker, user: User) -> Item:
    other_folder = await Item.create(
        owner=user,
        parent=None,
        name=faker.word(),
        type=Item.Type.FOLDER,
    )
    return await Item.create(
        owner=user,
        parent=other_folder,
        name=faker.file_name(),
        type=Item.Type.FILE,
        file_size=faker.random_int(1, 2**30),
    )


@pytest.fixture
async def sharing_link(faker: Faker, file: Item) -> SharingLink:
    return await SharingLink.create(
        item=file,
        token=faker.uuid4(),
        permission=faker.random_element(SharingLink.Permission),
    )


@pytest.fixture
def serialized_folder(user: User, folder: Item) -> dict[str, Any]:
    return {
        "id": folder.id,
        "create_time": any_str,
        "update_time": any_str,
        "owner_id": user.id,
        "parent_id": None,
        "name": folder.name,
        "type": folder.type,
        "file_size": folder.file_size,
    }


@pytest.fixture
def serialized_file(
    user: User,
    folder: Item,
    file: Item,
) -> dict[str, Any]:
    return {
        "id": file.id,
        "create_time": any_str,
        "update_time": any_str,
        "owner_id": user.id,
        "parent_id": folder.id,
        "name": file.name,
        "type": file.type,
        "file_size": file.file_size,
    }


@pytest.fixture
def serialized_sharing_link(file: Item, sharing_link: SharingLink) -> dict[str, Any]:
    return {
        "id": sharing_link.id,
        "create_time": any_str,
        "update_time": any_str,
        "item_id": file.id,
        "token": str(sharing_link.token),
        "permission": sharing_link.permission,
        "expire_time": None,
    }


@uses_db
class TestListUserItems:
    async def test_smoke(
        self,
        authed_client: AsyncClient,
        user: User,
        folder: Item,  # noqa: ARG002
        folder_other_user: Item,  # noqa: ARG002
        file: Item,  # noqa: ARG002
        serialized_folder: dict[str, Any],
    ) -> None:
        response = await authed_client.get(f"/users/{user.id}/items/")
        assert response.status_code == 200
        assert response.json() == {
            "items": [serialized_folder],
            "next_cursor": None,
        }

    async def test_other_org(
        self,
        authed_client: AsyncClient,
        user_other_org: User,
    ) -> None:
        response = await authed_client.get(f"/users/{user_other_org.id}/items/")
        assert response.status_code == 404

    async def test_not_found(self, authed_client: AsyncClient) -> None:
        response = await authed_client.get("/users/1/items/")
        assert response.status_code == 404


@uses_db
class TestListFolderItems:
    async def test_smoke(
        self,
        authed_client: AsyncClient,
        folder: Item,
        file: Item,  # noqa: ARG002,
        file_other_folder: Item,  # noqa: ARG002,
        serialized_file: dict[str, Any],
    ) -> None:
        response = await authed_client.get(f"/folders/{folder.id}/items/")
        assert response.status_code == 200
        assert response.json() == {
            "items": [serialized_file],
            "next_cursor": None,
        }

    async def test_other_org(
        self,
        authed_client: AsyncClient,
        folder_other_org: Item,
    ) -> None:
        response = await authed_client.get(f"/folders/{folder_other_org.id}/items/")
        assert response.status_code == 404

    async def test_not_found(self, authed_client: AsyncClient) -> None:
        response = await authed_client.get("/folders/1/items/")
        assert response.status_code == 404


@uses_db
class TestListItemSharingLinks:
    async def test_smoke(
        self,
        authed_client: AsyncClient,
        file: Item,
        sharing_link: SharingLink,  # noqa: ARG002
        serialized_sharing_link: dict[str, Any],
    ) -> None:
        response = await authed_client.get(f"/items/{file.id}/sharing-links/")
        assert response.status_code == 200
        assert response.json() == {
            "items": [serialized_sharing_link],
            "next_cursor": None,
        }

    async def test_other_org(
        self,
        authed_client: AsyncClient,
        file_other_org: Item,
    ) -> None:
        response = await authed_client.get(f"/items/{file_other_org.id}/sharing-links/")
        assert response.status_code == 404

    async def test_not_found(self, authed_client: AsyncClient) -> None:
        response = await authed_client.get("/items/1/sharing-links/")
        assert response.status_code == 404
