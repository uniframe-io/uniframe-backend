from typing import Optional

from fastapi import Request
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt

from server.apps.oauth.schemas import TokenPayload
from server.apps.user.crud import USER_CRUD
from server.apps.user.schemas import UserDO
from server.core import security
from server.libs.db.sqlalchemy import db
from server.settings import API_SETTING


def parse_user_from_request(request: Request) -> Optional[UserDO]:
    token: str = ""
    cookie_authorization = request.cookies.get("Authorization")
    if cookie_authorization is not None:
        cookie_scheme, cookie_param = get_authorization_scheme_param(
            cookie_authorization
        )

        if cookie_scheme.lower() == "bearer":
            token = cookie_param

    if not token:
        header_authorization = request.headers.get("Authorization")
        if header_authorization is not None:
            header_scheme, header_param = get_authorization_scheme_param(
                header_authorization
            )

            if header_scheme.lower() == "bearer":
                token = header_param

    if token:
        payload = jwt.decode(
            token, API_SETTING.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        with db():
            do_user = USER_CRUD.get_user(token_data.sub)
            return do_user
    return None
