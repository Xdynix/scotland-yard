from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSettings(BaseModel):
    user: str = "postgres"
    password: str = "postgres"  # noqa: S105
    host: str = "postgres"
    port: int = 5432
    database: str = "postgres"
    min_size: int = 1
    max_size: int = 100

    @property
    def url(self) -> str:
        return (
            f"postgres://{self.user}:{self.password}"
            f"@{self.host}:{self.port}"
            f"/{self.database}"
            f"?minsize={self.min_size}"
            f"&maxsize={self.max_size}"
        )


class JWTSettings(BaseModel):
    secret_key: str = "secret-key"  # noqa: S105
    algorithm: str = "HS256"


class AuthSettings(BaseModel):
    auth_code_expire_minutes: int = 15
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 3650  # 10 years


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    postgres: PostgresSettings = PostgresSettings()
    jwt: JWTSettings = JWTSettings()
    auth: AuthSettings = AuthSettings()


settings = Settings()

TORTOISE_ORM = {
    "connections": {
        "default": settings.postgres.url,
    },
    "apps": {
        "models": {
            "models": ["app.models"],
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}

JWT = settings.jwt

AUTH = settings.auth
