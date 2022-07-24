from typing import List

import pytest

from server.apps.user import schemas as user_schemas
from server.apps.user.crud import USER_CRUD
from server.core import security


def test_create_user() -> None:
    do_user_create = user_schemas.UserCreateDO(
        email="dummy.user@gmail.com",
        hashed_password=security.get_password_hash("dummy123456"),
        full_name="DummyUser",
        login_type=user_schemas.LOGIN_TYPE.EMAIL,
    )
    do_user = USER_CRUD.create_user(do_user_create)
    assert do_user.email == do_user_create.email
    assert do_user.full_name == do_user_create.full_name
    assert do_user.hashed_password == do_user_create.hashed_password
    assert do_user.login_type == do_user_create.login_type

    USER_CRUD.delete_user(do_user.id)

    return


def test_get_user(do_dummy_user: user_schemas.UserDO) -> None:
    # get a random user_id
    assert USER_CRUD.get_user(666666) is None

    do_user = USER_CRUD.get_user(do_dummy_user.id)

    assert do_user is not None
    assert do_user.email == do_dummy_user.email
    assert do_user.full_name == do_dummy_user.full_name
    assert do_user.is_active == do_dummy_user.is_active
    assert do_user.hashed_password == do_dummy_user.hashed_password
    assert do_user.is_superuser == do_dummy_user.is_superuser
    assert do_user.created_at == do_dummy_user.created_at
    assert do_user.updated_at == do_dummy_user.updated_at
    assert do_user.login_type == do_dummy_user.login_type


@pytest.mark.parametrize(
    "do_dummy_user_list", [2], indirect=["do_dummy_user_list"]
)
def test_get_all_users(
    do_dummy_user: user_schemas.UserDO,
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    all_user_l = USER_CRUD.get_all_users()

    assert len(all_user_l) == 3
    assert all_user_l[0].id == do_dummy_user.id
    assert all_user_l[1].id == do_dummy_user_list[0].id
    assert all_user_l[2].id == do_dummy_user_list[1].id

    # TODO: test is_active later

    return


def test_update_user() -> None:
    do_user_create = user_schemas.UserCreateDO(
        email="test_origin@gmail.com",
        hashed_password=security.get_password_hash("tester123456"),
        full_name="Test Dummy",
        login_type=user_schemas.LOGIN_TYPE.EMAIL,
    )
    do_user = USER_CRUD.create_user(do_user_create)

    user_update = user_schemas.UserUpdateDO(
        email="test_updated@gmail.com",
        hashed_password=security.get_password_hash("tester888888"),
        full_name="Updated Dummy",
    )
    do_updated_user = USER_CRUD.update_user(do_user.id, user_update)
    assert do_updated_user is not None
    assert do_updated_user.email == user_update.email
    assert do_updated_user.full_name == user_update.full_name
    assert do_updated_user.hashed_password == user_update.hashed_password

    USER_CRUD.delete_user(do_updated_user.id)
    return


def test_delete_user() -> None:
    # delete a random user id, just return None
    assert USER_CRUD.delete_user(666666) is None

    # create one user and delete
    do_user_create = user_schemas.UserCreateDO(
        email="dummy.user@gmail.com",
        hashed_password=security.get_password_hash("dummy123456"),
        full_name="DummyUser",
        login_type=user_schemas.LOGIN_TYPE.EMAIL,
    )
    do_user = USER_CRUD.create_user(do_user_create)
    USER_CRUD.delete_user(do_user.id)

    return


def test_get_user_by_email(do_dummy_user: user_schemas.UserDO) -> None:
    # check an random email
    assert do_dummy_user.login_type == user_schemas.LOGIN_TYPE.EMAIL

    assert USER_CRUD.get_user_by_email("no-exists@gmail.com") is None

    email = do_dummy_user.email
    if not email:
        return

    do_user = USER_CRUD.get_user_by_email(email)
    assert do_user is not None
    assert do_user.email == do_dummy_user.email
    assert do_user.full_name == do_dummy_user.full_name
    assert do_user.is_active == do_dummy_user.is_active
    assert do_user.hashed_password == do_dummy_user.hashed_password
    assert do_user.is_superuser == do_dummy_user.is_superuser
    assert do_user.created_at == do_dummy_user.created_at
    assert do_user.updated_at == do_dummy_user.updated_at
    assert do_user.login_type == do_dummy_user.login_type

    pass
