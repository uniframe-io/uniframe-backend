import datetime
import json
from datetime import timedelta
from typing import Generator, List

import pytest

from server.apps.oauth import schemas as oauth_schemas
from server.apps.oauth.crud import OAUTH_CRUD
from server.apps.user import schemas as user_schemas
from server.apps.user.crud import USER_CRUD

github_user_info = {
    "login": "DummyUser",
    "id": 88888888,
    "node_id": "XXXXXXXXXXXXXXXXXX",
    "avatar_url": "https://avatars.githubusercontent.com/u/88888888?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/DummyUser",
    "html_url": "https://github.com/DummyUser",
    "followers_url": "https://api.github.com/users/DummyUser/followers",
    "following_url": "https://api.github.com/users/DummyUser/following{/other_user}",
    "gists_url": "https://api.github.com/users/DummyUser/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/DummyUser/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/DummyUser/subscriptions",
    "organizations_url": "https://api.github.com/users/DummyUser/orgs",
    "repos_url": "https://api.github.com/users/DummyUser/repos",
    "events_url": "https://api.github.com/users/DummyUser/events{/privacy}",
    "received_events_url": "https://api.github.com/users/DummyUser/received_events",
    "type": "User",
    "site_admin": False,
    "name": "",
    "company": "",
    "blog": "",
    "location": "",
    "email": "",
    "hireable": "",
    "bio": "",
    "twitter_username": "",
    "public_repos": 5,
    "public_gists": 0,
    "followers": 31,
    "following": 50,
    "created_at": "2015-08-21T06:24:42Z",
    "updated_at": "2021-04-09T14:17:10Z",
}


@pytest.fixture()
def do_dummy_oauth2() -> Generator[oauth_schemas.OAuth2UserDo, None, None]:
    """
    do_dummy_oauth2 is a fixture to generate a dummy oauth2 for unit tests
    """
    do_oauth2_create = oauth_schemas.OAuth2UserCreateDO(
        full_name="dummy_oauth2_user",
        login_type=user_schemas.LOGIN_TYPE.OAUTH2_GITHUB,
        provider=oauth_schemas.OAUTH2_PROVIDER_TYPE.PROVIDER_GITHUB,
        provider_id=88888888,
        ext_info=json.dumps(github_user_info),
    )
    do_dummy_oauth2 = OAUTH_CRUD.create_oauth2_user(do_oauth2_create)

    yield do_dummy_oauth2

    OAUTH_CRUD.delete_oauth2_user(do_dummy_oauth2.id)
    USER_CRUD.delete_user(do_dummy_oauth2.owner_id)


def test_get_oauth2_user(do_dummy_oauth2: oauth_schemas.OAuth2UserDo) -> None:

    do_oauth2 = OAUTH_CRUD.get_oauth2_user(
        do_dummy_oauth2.provider, do_dummy_oauth2.provider_id
    )
    assert do_oauth2 == do_dummy_oauth2

    return


def test_create_oauth2_user() -> None:
    do_oauth2_create = oauth_schemas.OAuth2UserCreateDO(
        full_name="dummy_oauth2_user",
        login_type=user_schemas.LOGIN_TYPE.OAUTH2_GITHUB,
        provider=oauth_schemas.OAUTH2_PROVIDER_TYPE.PROVIDER_GITHUB,
        provider_id=88888888,
        ext_info=json.dumps(github_user_info),
    )
    do_dummy_oauth2 = OAUTH_CRUD.create_oauth2_user(do_oauth2_create)

    assert do_dummy_oauth2.provider_id == do_oauth2_create.provider_id

    OAUTH_CRUD.delete_oauth2_user(do_dummy_oauth2.id)
    USER_CRUD.delete_user(do_dummy_oauth2.owner_id)

    return


@pytest.fixture()
def do_dummy_vcode(
    do_dummy_user: user_schemas.UserDO,
) -> Generator[oauth_schemas.VerificationCodeDO, None, None]:
    """
    do_dummy_vcode is a fixture to generate a dummy verification code for unit tests
    """
    vcode_create = oauth_schemas.VerificationCodeCreateDO(
        email=do_dummy_user.email,
        action=oauth_schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD,
        vcode="183020",
        owner_id=do_dummy_user.id,
        expire_at=datetime.datetime.utcnow() + timedelta(minutes=10),
    )
    do_dummy_vcode = OAUTH_CRUD.create_vcode(vcode_create)

    yield do_dummy_vcode

    OAUTH_CRUD.delete_vcode(do_dummy_vcode.id)


@pytest.fixture()
def do_dummy_vcode_list(
    do_dummy_user: user_schemas.UserDO,
) -> Generator[List[oauth_schemas.VerificationCodeDO], None, None]:
    """
    do_dummy_vcode is a fixture to generate a dummy verification code for unit tests
    """
    do_dummy_vcode_list = []
    for vcode in ("183020", "183021"):
        vcode_create = oauth_schemas.VerificationCodeCreateDO(
            email=do_dummy_user.email,
            action=oauth_schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD,
            vcode=vcode,
            owner_id=do_dummy_user.id,
            expire_at=datetime.datetime.utcnow() + timedelta(minutes=10),
        )
        do_dummy_vcode = OAUTH_CRUD.create_vcode(vcode_create)
        do_dummy_vcode_list.append(do_dummy_vcode)

    yield do_dummy_vcode_list

    for c in do_dummy_vcode_list:
        OAUTH_CRUD.delete_vcode(c.id)


def test_get_vcode(do_dummy_vcode: oauth_schemas.VerificationCodeDO) -> None:
    do_vcode = OAUTH_CRUD.get_vcode(do_dummy_vcode.action, do_dummy_vcode.email)
    assert do_vcode is not None
    assert do_vcode.is_active is True


def test_create_vcode(do_dummy_user: user_schemas.UserDO) -> None:
    vcode_create = oauth_schemas.VerificationCodeCreateDO(
        email=do_dummy_user.email,
        action=oauth_schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD,
        vcode="183020",
        expire_at=datetime.datetime.utcnow() + timedelta(minutes=10),
    )
    do_dummy_vcode = OAUTH_CRUD.create_vcode(vcode_create)

    assert do_dummy_vcode.vcode == "183020"

    OAUTH_CRUD.delete_vcode(do_dummy_vcode.id)


def test_create_vcode_count(
    do_dummy_user: user_schemas.UserDO,
    do_dummy_vcode_list: List[oauth_schemas.VerificationCodeDO],
) -> None:
    cnt = OAUTH_CRUD.get_vcode_count(oauth_schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD, do_dummy_user.email)  # type: ignore

    assert cnt == 2


def test_delete_vcode_by_action(
    do_dummy_user: user_schemas.UserDO,
    do_dummy_vcode_list: List[oauth_schemas.VerificationCodeDO],
) -> None:
    OAUTH_CRUD.delete_vcode_by_action(oauth_schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD, do_dummy_user.email)  # type: ignore
    do_vcode = OAUTH_CRUD.get_vcode(oauth_schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD, do_dummy_user.email)  # type: ignore
    assert do_vcode is None


def test_update_oauth2_user(
    do_dummy_oauth2: oauth_schemas.OAuth2UserDo,
) -> None:

    OAUTH_CRUD.update_oauth2_user(
        do_dummy_oauth2.owner_id,
        oauth_schemas.OAuth2UserUpdateDO(is_active=False, ext_info="deleted"),
    )

    do_oauth2 = OAUTH_CRUD.get_oauth2_user(
        do_dummy_oauth2.provider, do_dummy_oauth2.provider_id
    )

    assert do_oauth2 is not None
    if do_oauth2:
        assert do_oauth2.is_active is False

    return
