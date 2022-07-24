import traceback
from typing import Optional

from fastapi import Depends, Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt
from pydantic import ValidationError

from server.apps.oauth.schemas import TokenPayload
from server.apps.user.crud import USER_CRUD
from server.apps.user.schemas import UserDO
from server.core import security
from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING
from server.settings.logger import api_logger as logger


class OAuth2PasswordBearerCookie(OAuth2):
    """
    This is a bearer token validation from both header and cookie
    https://medium.com/data-rebels/fastapi-how-to-add-basic-and-cookie-authentication-a45c85ef47d3
    """

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            password={"tokenUrl": tokenUrl, "scopes": scopes}
        )
        super().__init__(
            flows=flows, scheme_name=scheme_name, auto_error=auto_error
        )

    async def __call__(self, request: Request) -> Optional[str]:
        cookie_authorization = request.cookies.get("Authorization")
        if cookie_authorization is not None:
            cookie_scheme, cookie_param = get_authorization_scheme_param(
                cookie_authorization
            )

            if cookie_scheme.lower() == "bearer":
                param = cookie_param
                return param
            else:
                if self.auto_error:
                    logger.error(
                        f"API__INVALID_AUTHORIZATOIN_SCHEMA: No valid authorization token from cookie! cookie_schem [{cookie_scheme}]"
                    )
                    raise EXCEPTION_LIB.API__INVALID_AUTHORIZATOIN_SCHEMA.value(
                        "No valid authorization token from cookie. Please login in again."
                    )
                else:
                    return None

        header_authorization = request.headers.get("Authorization")
        if header_authorization is not None:
            header_scheme, header_param = get_authorization_scheme_param(
                header_authorization
            )

            if header_scheme.lower() == "bearer":
                param = header_param
                return param
            else:
                if self.auto_error:
                    logger.error(
                        f"API__INVALID_AUTHORIZATOIN_SCHEMA: No valid authorization token from header! cookie_schem [{header_scheme}]"
                    )
                    raise EXCEPTION_LIB.API__INVALID_AUTHORIZATOIN_SCHEMA.value(
                        "No valid authorization token from header. Please login again."
                    )
                else:
                    return None

        logger.error(
            "API__INVALID_AUTHORIZATOIN_SCHEMA: No valid authorization token from header or cookie"
        )
        raise EXCEPTION_LIB.API__INVALID_AUTHORIZATOIN_SCHEMA.value(
            "No valid authorization token from header or cookie. Please login again"
        )


# OAuth2PasswordBearer is a tool that FastAPI uses to implement security features
# https://fastapi.tiangolo.com/tutorial/security/first-steps/#fastapis-oauth2passwordbearer
# reusable_oauth2 = OAuth2PasswordBearer(
#     tokenUrl=f"{API_SETTING.API_V1_STR}/login/"
# )

# instead of using FastAPI OAuth2PasswordBearer, we use the customized OAuth2PasswordBearerCookie
# so that it can handle token in header and in cookie
reusable_oauth2 = OAuth2PasswordBearerCookie(
    tokenUrl=f"{API_SETTING.API_V1_STR}/login/"
)


def get_current_user(token: str = Depends(reusable_oauth2)) -> UserDO:
    """Get the current login user
    This is the standard way how fastapi handle security, authentication and authorization
    https://fastapi.tiangolo.com/tutorial/security/

    `get_current_user` is used as `dependencies` in the endpoint which enforce security and authentication
    Please read https://fastapi.tiangolo.com/tutorial/dependencies/ for more details
    """
    try:
        payload = jwt.decode(
            token, API_SETTING.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        traceback.print_exc()
        logger.error(
            "API__VALIDATE_CRDENTIALS_ERROR： Could not validate credentials! jwt token invalid. Some reasons: 1) server jwt secret change 2) jwt token from user cookie damaged"
        )
        raise EXCEPTION_LIB.API__VALIDATE_CRDENTIALS_ERROR.value(
            "Could not validate credentials. Please logout and login again or input the right JWT token",
        )
    user = USER_CRUD.get_user(token_data.sub)
    if not user:
        logger.error(
            f"USER__USER_ID_NOT_EXIST: decoded jwt token does not include a valid user id! user_id [{token_data.sub}]"
        )
        raise EXCEPTION_LIB.USER__USER_ID_NOT_EXIST.value(
            "The credential is not valid! Please logout and login again or input the right JWT token"
        )

    return user


def get_current_active_user(
    current_user: UserDO = Depends(get_current_user),
) -> UserDO:
    """Return the current login user if it is a active user"""
    if not current_user.is_active:
        logger.error(f"API__INACTIVE_USER: user_id [{current_user.id}]")
        raise EXCEPTION_LIB.API__INACTIVE_USER.value(
            "Your login user is inactive. Please contact the administrator"
        )
    return current_user


def get_current_active_superuser(
    current_user: UserDO = Depends(get_current_active_user),
) -> UserDO:
    """Return the current login user if it is a superuser"""
    if not current_user.is_superuser:
        logger.error(
            f"API__NO_ENOUGH_PRIVILEGE: current action needs a super user. Current user [{current_user.id}] is not a super user"
        )
        raise EXCEPTION_LIB.API__NO_ENOUGH_PRIVILEGE.value(
            "This action is only authorized by a super user"
        )
    return current_user


def get_current_active_normal_user(
    current_user: UserDO = Depends(get_current_active_user),
) -> UserDO:
    """Return the current login user if it is a normal user"""
    if current_user.is_superuser:
        logger.error(
            f"API__NOT_A_REQUIED_USER_GROUP: this action only works for normal user, but current user [{current_user.id}] is a super user"
        )
        raise EXCEPTION_LIB.API__NOT_A_REQUIED_USER_GROUP.value(
            "This action is only authorized for a normal user"
        )
    return current_user
