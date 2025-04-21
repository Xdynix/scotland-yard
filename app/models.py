from enum import StrEnum
from uuid import uuid4

from tortoise import fields, models


class BaseModel(models.Model):
    id = fields.BigIntField(primary_key=True)
    create_time = fields.DatetimeField(auto_now_add=True)
    update_time = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(BaseModel):
    name = fields.CharField(max_length=255)

    users: fields.ReverseRelation["User"]

    def __str__(self) -> str:
        return f"Organization: {self.name}"


class User(BaseModel):
    class Role(StrEnum):
        REGULAR = "regular"
        ADMIN = "admin"

    organization: fields.ForeignKeyRelation[Organization] = fields.ForeignKeyField(
        "models.Organization",
        related_name="users",
    )

    username = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255)
    active = fields.BooleanField(default=True)
    role = fields.CharEnumField(Role, max_length=64, default=Role.REGULAR)
    first_name = fields.CharField(max_length=255, default="")
    last_name = fields.CharField(max_length=255, default="")

    items: fields.ReverseRelation["Item"]

    class Meta:
        unique_together = (
            ("organization", "username"),
            ("organization", "email"),
        )

    def __str__(self) -> str:
        return f"User: {self.username}"


class Item(BaseModel):
    class Type(StrEnum):
        FILE = "file"
        FOLDER = "folder"

    owner: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User",
        related_name="items",
    )
    parent: fields.ForeignKeyRelation["Item"] | None = fields.ForeignKeyField(
        "models.Item",
        related_name="children",
        null=True,
    )

    name = fields.CharField(max_length=255)
    type = fields.CharEnumField(Type, max_length=64)
    file_size = fields.BigIntField(default=0)

    children: fields.ReverseRelation["Item"]
    sharing_links: fields.ReverseRelation["SharingLink"]

    class Meta:
        unique_together = (("parent", "name"),)
        indexes = (
            ("parent", "owner"),
            ("owner", "type"),
        )

    def __str__(self) -> str:
        return f"{self.type.capitalize()}: {self.name}"


class SharingLink(BaseModel):
    class Permission(StrEnum):
        READ = "read"
        WRITE = "write"

    item: fields.ForeignKeyRelation[Item] = fields.ForeignKeyField(
        "models.Item",
        related_name="sharing_links",
    )

    token = fields.UUIDField(unique=True, default=uuid4)
    permission = fields.CharEnumField(Permission, max_length=64)
    expire_time = fields.DatetimeField(null=True, default=None)

    def __str__(self) -> str:
        return f"Sharing Link: {self.token}"
