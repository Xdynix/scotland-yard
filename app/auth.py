__all__ = ("OAuthRequestSource",)

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated, Any, Literal, cast
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel, Field, HttpUrl

from . import settings
from .types import Id, Token

jwt_settings = settings.JWT
auth_settings = settings.AUTH

router = APIRouter(
    prefix="",
    tags=["auth"],
)


class OAuthError(StrEnum):
    INVALID_GRANT = "invalid_grant"
    UNSUPPORTED_GRANT_TYPE = "unsupported_grant_type"


class OAuthException(Exception):
    def __init__(self, error: OAuthError):
        self.error = error


class TokenType(StrEnum):
    AUTH_CODE = "auth_code"
    ACCESS_TOKEN = "access_token"  # noqa: S105
    REFRESH_TOKEN = "refresh_token"  # noqa: S105


class AuthCodeResponse(BaseModel):
    auth_code: Token


def create_jwt(data: dict[str, Any], expires_in: timedelta, type_: TokenType) -> Token:
    payload: dict[str, Any] = {
        **data,
        "exp": datetime.now(tz=UTC) + expires_in,
        "iat": datetime.now(tz=UTC),
        "type": type_,
        "nonce": uuid4().hex,
    }
    return jwt.encode(
        payload,
        key=jwt_settings.secret_key,
        algorithm=jwt_settings.algorithm,
    )


def verify_jwt(token: Token, type_: TokenType) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        key=jwt_settings.secret_key,
        algorithms=[jwt_settings.algorithm],
    )
    if payload.get("type") != type_:
        raise jwt.InvalidTokenError
    return cast(dict[str, Any], payload)


@router.get("/authorize")
def authorize(
    client_id: Id,
    redirect_uri: HttpUrl,
    state: Annotated[str, Field(max_length=512)] = "",
) -> RedirectResponse:
    auth_code = create_jwt(
        data={"sub": str(client_id)},
        expires_in=timedelta(minutes=auth_settings.auth_code_expire_minutes),
        type_=TokenType.AUTH_CODE,
    )

    uri = str(redirect_uri)
    scheme, netloc, path, query, fragment = urlsplit(uri)

    params = parse_qs(query, keep_blank_values=True)
    params["code"] = [auth_code]
    params["state"] = [state]

    new_query = urlencode(params, doseq=True)
    full_redirect = urlunsplit((scheme, netloc, path, new_query, fragment))

    return RedirectResponse(full_redirect)


class TokenRequest(BaseModel):
    grant_type: str
    code: Token = ""
    refresh_token: Token = ""


class TokenResponse(BaseModel):
    access_token: Token
    refresh_token: Token
    expires_in: float
    token_type: Literal["bearer"] = "bearer"  # noqa: S105


@router.post("/token")
def token(request: Annotated[TokenRequest, Form()]) -> TokenResponse:
    try:
        match request.grant_type:
            case "authorization_code":
                payload = verify_jwt(request.code, type_=TokenType.AUTH_CODE)
                refresh_token = ""
            case "refresh_token":
                payload = verify_jwt(
                    request.refresh_token, type_=TokenType.REFRESH_TOKEN
                )
                refresh_token = request.refresh_token
            case _:
                raise OAuthException(OAuthError.UNSUPPORTED_GRANT_TYPE)
    except jwt.InvalidTokenError as e:
        raise OAuthException(OAuthError.INVALID_GRANT) from e

    claims = {"sub": payload["sub"]}
    access_token_expire_in = timedelta(
        minutes=auth_settings.access_token_expire_minutes,
    )
    access_token = create_jwt(
        data=claims,
        expires_in=access_token_expire_in,
        type_=TokenType.ACCESS_TOKEN,
    )
    if not refresh_token:
        refresh_token_expire_in = timedelta(
            minutes=auth_settings.refresh_token_expire_minutes,
        )
        refresh_token = create_jwt(
            data=claims,
            expires_in=refresh_token_expire_in,
            type_=TokenType.REFRESH_TOKEN,
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_token_expire_in.total_seconds(),
    )


oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=router.url_path_for("authorize"),
    tokenUrl=router.url_path_for("token"),
)


class RequestSource(BaseModel):
    organization_id: Id


def get_request_source(token: Annotated[str, Depends(oauth2_scheme)]) -> RequestSource:
    try:
        payload = verify_jwt(token, type_=TokenType.ACCESS_TOKEN)
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from e
    return RequestSource(organization_id=payload["sub"])


OAuthRequestSource = Annotated[RequestSource, Depends(get_request_source)]


@router.get("/me")
def get_me(rs: OAuthRequestSource) -> OAuthRequestSource:
    return rs
