from typing import List

import pytest

from server.apps.group import schemas
from server.apps.group.crud import GROUP_CRUD
from server.apps.group.utils import (
    is_group_active,
    is_user_group_owner,
    is_user_group_viewer,
)
from server.apps.user import schemas as user_schemas


def test_is_group_active(do_dummy_group: schemas.GroupDO) -> None:
    assert is_group_active(do_dummy_group)


def test_is_user_group_owner(
    do_dummy_user: user_schemas.UserDO, do_dummy_group: schemas.GroupDO
) -> None:
    assert is_user_group_owner(do_dummy_group, do_dummy_user.id)


@pytest.mark.parametrize(
    "do_dummy_user_list,do_dummy_group_list",
    [(2, 2)],
    indirect=["do_dummy_user_list", "do_dummy_group_list"],
)
def test_is_user_group_viewer(
    do_dummy_user_list: List[user_schemas.UserDO],
    do_dummy_group_list: List[schemas.GroupDO],
) -> None:
    # use dummy users and group to construct the test cases
    GROUP_CRUD.add_group_member(
        do_dummy_group_list[0].id, do_dummy_user_list[0].id
    )
    GROUP_CRUD.add_group_member(
        do_dummy_group_list[1].id, do_dummy_user_list[0].id
    )

    assert is_user_group_viewer(
        do_dummy_group_list[0].id, do_dummy_user_list[0].id
    )
    assert is_user_group_viewer(
        do_dummy_group_list[1].id, do_dummy_user_list[0].id
    )

    assert not is_user_group_viewer(
        do_dummy_group_list[0].id, do_dummy_user_list[1].id
    )
    assert not is_user_group_viewer(
        do_dummy_group_list[1].id, do_dummy_user_list[1].id
    )

    # release resources
    GROUP_CRUD.delete_group_member(
        do_dummy_group_list[0].id, do_dummy_user_list[0].id
    )
    GROUP_CRUD.delete_group_member(
        do_dummy_group_list[1].id, do_dummy_user_list[0].id
    )
