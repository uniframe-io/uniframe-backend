from http.cookies import SimpleCookie
from typing import Dict

import pytest
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.testclient import TestClient
from jose import jwt
from requests.models import Response

from api_tests import pytest_utils
from api_tests.conftest import DUMMY_USER_EMAIL, DUMMY_USER_PASSWORD
from server.apps.user import schemas as user_schemas
from server.apps.user.crud import USER_CRUD
from server.core import security
from server.core.exception import EXCEPTION_LIB, NmBaseException
from server.settings import API_SETTING


def assert_cookie_token(response: Response, user_id: int) -> None:
    # the cookie is in header with "set-cookie" as key
    # the only way I found to validate cookie is
    # https://stackoverflow.com/a/21522721
    cookie: SimpleCookie = SimpleCookie()
    cookie.load(response.headers["set-cookie"])

    # check that token exists in cookie and has user encoded within it
    cookie_authorization = cookie.get("Authorization")
    assert cookie_authorization is not None

    _, token = get_authorization_scheme_param(cookie_authorization.value)
    creds = jwt.decode(
        token, API_SETTING.SECRET_KEY, algorithms=security.ALGORITHM
    )
    assert "sub" in creds
    assert creds["sub"] == str(user_id)
    assert "exp" in creds


def test_login_correct(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
) -> None:
    api_client.headers["content-type"] = "application/x-www-form-urlencoded"
    login_data = {"username": DUMMY_USER_EMAIL, "password": DUMMY_USER_PASSWORD}
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/login", data=login_data
    )

    assert response.status_code == 200
    print(response.headers)
    assert_cookie_token(response, do_dummy_user.id)


@pytest.mark.parametrize(
    # TODO: add test for inactive user!
    "email, password, exception_err",
    (
        (
            "nobody@nobody.com",
            "nobody",
            EXCEPTION_LIB.API__VALIDATE_CRDENTIALS_ERROR,
        ),
        (
            DUMMY_USER_EMAIL,
            "wrong_password",
            EXCEPTION_LIB.API__VALIDATE_CRDENTIALS_ERROR,
        ),
    ),
)
def test_user_with_wrong_creds_doesnt_receive_token(
    api_client: TestClient,
    email: str,
    password: str,
    exception_err: NmBaseException,
) -> None:
    api_client.headers["content-type"] = "application/x-www-form-urlencoded"
    login_data = {"username": email, "password": password}
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/login", data=login_data
    )
    pytest_utils.assert_endpoint_response(
        response,
        exception_err.value("must have this placeholder string!"),  # type: ignore
    )


def test_test_token(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
    dummy_user_token_header: Dict[str, str],
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/test-token",
        headers=dummy_user_token_header,
    )

    assert response.status_code == 200
    dto_user = user_schemas.UserDTO(**response.json())
    assert dto_user.full_name == do_dummy_user.full_name
    assert dto_user.id == do_dummy_user.id
    assert dto_user.email == do_dummy_user.email
    assert dto_user.created_at == do_dummy_user.created_at


def test_signup_correct(
    api_client: TestClient,
) -> None:
    SIGN_UP_TEST_EMAIL = "signup_test@google.com"
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/signup",
        json=user_schemas.UserCreateDTO(
            email=SIGN_UP_TEST_EMAIL,
            password="signup",
            full_name="Sign Up Test User",
            vcode="123456",
        ).dict(),  # Important!!! json expect a dictionary
    )
    assert response.status_code == 200

    # get the user id by email
    do_user = USER_CRUD.get_user_by_email(SIGN_UP_TEST_EMAIL)
    assert do_user is not None

    assert response.json() == "Sign-up successfully"

    USER_CRUD.delete_user(do_user.id)


def test_signup_wrong(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/signup",
        json=user_schemas.UserCreateDTO(
            email=DUMMY_USER_EMAIL,
            password="signup",
            full_name="Sign Up Test User",
            vcode="123456",
        ).dict(),  # Important!!! json expect a dictionary
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.USER__EMAIL_ALREADY_EXISTS.value(
            "must have this placeholder string!"
        ),
    )


def test_reset_password_correct(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
    dummy_user_token_header: Dict,
) -> None:
    # change dummy password to something else
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/reset-password",
        headers=dummy_user_token_header,
        json=user_schemas.UserResetPasswordDTO(
            old_password=DUMMY_USER_PASSWORD, new_password="temp_password"
        ).dict(),  # Important!!! json expect a dictionary
    )
    assert response.json() == "Password updated successfully"

    # change it back
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/reset-password",
        headers=dummy_user_token_header,
        json=user_schemas.UserResetPasswordDTO(
            old_password="temp_password", new_password=DUMMY_USER_PASSWORD
        ).dict(),  # Important!!! json expect a dictionary
    )
    assert response.json() == "Password updated successfully"


def test_reset_password_wrong(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
    dummy_user_token_header: Dict,
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/reset-password",
        headers=dummy_user_token_header,
        json=user_schemas.UserResetPasswordDTO(
            old_password="temp_password", new_password="temp_password"
        ).dict(),  # Important!!! json expect a dictionary
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.USER__RESET_PASSWORD_ERROR.value(
            "must have this placeholder string!"
        ),
    )

    # change dummy password to something else
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/reset-password",
        headers=dummy_user_token_header,
        json=user_schemas.UserResetPasswordDTO(
            old_password="wrong_password", new_password="temp_password"
        ).dict(),  # Important!!! json expect a dictionary
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.API__VALIDATE_CRDENTIALS_ERROR.value(
            "must have this placeholder string!"
        ),
    )


def test_deactivate(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
    dummy_user_token_header: Dict,
) -> None:
    # change dummy password to something else
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/deactivate",
        headers=dummy_user_token_header,
    )

    assert response.status_code == 200
    assert response.json() == "Deactivate account successfully"


def test_login_with_wrong_type(
    api_client: TestClient,
    do_dummy_oauth2_user: user_schemas.UserDO,
) -> None:
    api_client.headers["content-type"] = "application/x-www-form-urlencoded"
    login_data = {
        "username": "dummy_oauth2_user@gmail.com",
        "password": "123456",
    }
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/login", data=login_data
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.USER__LOGIN_TYPE_ERROR.value(
            "must have this placeholder string!"
        ),
    )


def test_reset_password_with_wrong_login_type(
    api_client: TestClient,
    do_dummy_oauth2_user: user_schemas.UserDO,
    dummy_oauth2_user_token_header: Dict,
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/reset-password",
        headers=dummy_oauth2_user_token_header,
        json=user_schemas.UserResetPasswordDTO(
            old_password=DUMMY_USER_PASSWORD, new_password="temp_password"
        ).dict(),
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.USER__LOGIN_TYPE_ERROR.value(
            "must have this placeholder string!"
        ),
    )
