import pytest
from faker import Faker

from app.models import Item, Organization, SharingLink, User


class TestOrganization:
    def test_str(self, faker: Faker) -> None:
        name = faker.company()
        organization = Organization(name=name)
        assert str(organization) == f"Organization: {name}"


class TestUser:
    def test_str(self, faker: Faker) -> None:
        username = faker.user_name()
        user = User(username=username)
        assert str(user) == f"User: {username}"


class TestItem:
    @pytest.mark.parametrize("item_type", Item.Type)
    def test_str(self, faker: Faker, item_type: Item.Type) -> None:
        name = faker.file_name()
        item = Item(name=name, type=item_type)
        match item_type:
            case Item.Type.FILE:
                assert str(item) == f"File: {name}"
            case Item.Type.FOLDER:
                assert str(item) == f"Folder: {name}"


class TestSharingLink:
    def test_str(self, faker: Faker) -> None:
        token = faker.uuid4()
        sharing_link = SharingLink(token=token)
        assert str(sharing_link) == f"Sharing Link: {token}"
