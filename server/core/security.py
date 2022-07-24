import os
from datetime import datetime, timedelta
from typing import Any, Optional, Union
from urllib.parse import urlparse

from fastapi import Response
from jose import jwt
from passlib.context import CryptContext

from server.settings import API_SETTING
from server.settings.logger import api_logger as logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=API_SETTING.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, API_SETTING.SECRET_KEY, algorithm=ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def set_token_cookie(
    response: Response,
    access_token: Optional[str],
    max_age: int,
    origin: str = None,
) -> None:
    """
    This is a helper function for setting up cookie
    so that we can control the samesite, security
    """

    if access_token is not None:
        value = f"Bearer {access_token}"
    else:
        value = ""

    # if backend server is just for local testing
    if (
        API_SETTING.COOKIE_DOMAIN == "localhost"
        or os.getenv("API_RUN_LOCATION") == "minikube"
    ):
        # set cookies for localhost and minikube deployment
        # secure must be False, since http is used
        logger.info(
            "set cookie for http mode in localhost (docker-compose) and minikube"
        )
        response.set_cookie(
            key="Authorization",
            value=value,
            httponly=False,
            max_age=max_age,
            expires=max_age,
        )
        return

    # only frontend dev/debug locally, same cookie as samesite=None
    samesite = "lax"
    if origin is not None:
        logger.info("set cookie for frontend dev/debug locally")
        parsed_uri = urlparse(origin)
        hostname = parsed_uri.hostname
        if hostname in ["localhost", "127.0.0.1"]:
            samesite = "None"

    response.set_cookie(
        key="Authorization",
        value=value,
        domain=API_SETTING.COOKIE_DOMAIN,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite=samesite,
        secure=True,
    )

    return


def add_token_cookie(
    response: Response, access_token: str, origin: str = None
) -> None:
    """
    Server side add cookie when login, oauth login, etc
    """
    set_token_cookie(
        response=response,
        access_token=access_token,
        # N.B. max_age is in unit of seconds
        max_age=API_SETTING.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        origin=origin,
    )
    return


def delete_token_cookie(response: Response, origin: str = None) -> None:
    """
    Server side delete cookie when logout, reset password, deactivate, etc
    N.B. we don't use the fastapi response delete cookie function
    because we want to control samesite and secure field
    """
    set_token_cookie(
        response=response, access_token=None, max_age=0, origin=origin
    )

    return
