from typing import Any

import requests
from behave import given, then, when
from behave.runner import Context
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt

from integration_tests.utils import url_gen
from server.apps.user import schemas as user_schemas
from server.core import security
from server.settings import API_SETTING


@given("backend is setup")
def step_impl_1(context: Context) -> Any:
    assert True


@given(
    'I sign up with email "{email}" and name "{full_name}" and password "{password}"'
)
@when(
    'I sign up with email "{email}" and name "{full_name}" and password "{password}"'
)
def setp_impl_2(
    context: Context, email: str, full_name: str, password: str
) -> None:
    data = user_schemas.UserCreateDTO(
        email=email,
        password=password,
        full_name=full_name,
        vcode="123456",
    ).dict()

    r = requests.post(url=url_gen("signup"), json=data)
    print(r.status_code)
    print(r.json())
    assert r.status_code == 200
    context.resp_body = r.json()


@given('I login with email "{email}" and password "{password}"')
@when('I login with email "{email}" and password "{password}"')
def setp_impl_3(context: Context, email: str, password: str) -> None:
    payload = {"username": email, "password": password}

    sess = requests.Session()
    r = sess.post(url=url_gen("login"), data=payload)

    assert r.status_code == 200
    context.sess = sess
    context.resp_body = r.json()
    context.resp_header = r.headers


@then('I should see response body with string "{response_str}"')
def setp_impl_4(context: Context, response_str: str) -> None:
    resp = context.resp_body
    assert resp == response_str


@then('I should see response body with email "{email}" and name "{full_name}"')
def setp_impl_5(context: Context, email: str, full_name: str) -> None:
    user = context.resp_body.get("user")
    assert user["email"] == email
    assert user["full_name"] == full_name


@then("I should see response body with JWT token")
def setp_impl_6(context: Context) -> None:
    token = context.resp_body.get("access_token")

    creds = jwt.decode(
        token, API_SETTING.SECRET_KEY, algorithms=security.ALGORITHM
    )
    assert "sub" in creds
    assert "exp" in creds

    user = context.resp_body.get("user")
    assert creds["sub"] == str(user["id"])


@then("I should see cookie be setup")
def setp_impl_7(context: Context) -> None:
    cookie_authorization = context.sess.cookies.get_dict().get("Authorization")
    assert cookie_authorization is not None

    # N.B. remove double quote
    cookie_authorization = cookie_authorization[1:-1]

    _, token = get_authorization_scheme_param(cookie_authorization)

    creds = jwt.decode(
        token, API_SETTING.SECRET_KEY, algorithms=security.ALGORITHM
    )
    assert "sub" in creds
    assert "exp" in creds

    user = context.resp_body.get("user")
    assert creds["sub"] == str(user["id"])
