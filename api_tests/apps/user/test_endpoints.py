from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from api_tests import pytest_utils
from server.apps.user import schemas as user_schemas
from server.apps.user.crud import USER_CRUD
from server.core import security
from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING


def test_create_group(
    api_client: TestClient,
    super_user_token_header: Dict[str, str],
    do_dummy_user: user_schemas.UserDO,
) -> None:
    # create another user with the same name, an exception should be raised
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/users",
        headers=super_user_token_header,
        json=user_schemas.UserCreateDTO(
            email=do_dummy_user.email,
            password="test123456",
            full_name="Test User",
            vcode="123456",
        ).dict(),  # Important!!! json expect a dictionary
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.USER__EMAIL_ALREADY_EXISTS.value(
            "must have this placeholder string!"
        ),
    )

    # sanity check of creating a group
    user_create_dto = user_schemas.UserCreateDTO(
        email="test_endpoint@gamil.com",
        password="test123456",
        full_name="Test User",
        vcode="123456",
    )
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/users",
        headers=super_user_token_header,
        json=user_create_dto.dict(),  # Important!!! json expect a dictionary
    )

    assert response.status_code == 200
    dto_user = user_schemas.UserDTO(**response.json())
    assert dto_user is not None
    assert dto_user.email == user_create_dto.email
    assert dto_user.full_name == user_create_dto.full_name

    # release the resource
    USER_CRUD.delete_user(dto_user.id)

    return


@pytest.mark.parametrize(
    "do_dummy_user_list",
    [3],
    indirect=["do_dummy_user_list"],
)
def test_get_all_groups(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
    super_user_token_header: Dict[str, str],
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    # get all groups from dummy user, should has only one group
    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/users",
        headers=super_user_token_header,
    )
    assert response.status_code == 200
    # we should have 5 users created in the database
    # - 1 super user
    # - 1 dummy user
    # - 3 users in dummy user list
    assert len(response.json()) == 5

    # Create a new user
    do_user_create = user_schemas.UserCreateDO(
        email="dummy.user@gmail.com",
        hashed_password=security.get_password_hash("dummy123456"),
        full_name="DummyUser",
        login_type=user_schemas.LOGIN_TYPE.EMAIL,
    )
    do_user = USER_CRUD.create_user(do_user_create)

    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/users",
        headers=super_user_token_header,
    )
    assert response.status_code == 200
    # Now we should have 6 users
    assert len(response.json()) == 6

    # release the resource
    USER_CRUD.delete_user(do_user.id)

    return
