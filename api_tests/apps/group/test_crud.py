from typing import List

import pytest

from server.apps.group import schemas
from server.apps.group.crud import GROUP_CRUD
from server.apps.user import schemas as user_schemas
from server.core.exception import EXCEPTION_LIB


def test_get_group(do_dummy_user: user_schemas.UserDO) -> None:
    # if the group doesn't exist, it should return None
    assert GROUP_CRUD.get_group(999999999) is None

    group_create = schemas.GroupCreateDO(
        name="test_group", description="description blablablab ..."
    )

    # create a group, and check if we can get it
    do_group = GROUP_CRUD.create_group(group_create, user_id=do_dummy_user.id)

    do_group_get = GROUP_CRUD.get_group(do_group.id)
    assert do_group_get == do_group

    # release the resource
    GROUP_CRUD.delete_group(do_group.id)
    return


def test_get_all_groups_owned_by_user(
    do_dummy_user: user_schemas.UserDO,
) -> None:
    # if the user_id doesn't exist, it should return None
    assert GROUP_CRUD.get_all_groups_owned_by_user(999999999) == []

    # get groups of dummy user
    # since we have created one dummy group in conftest.py, we should get one group
    assert GROUP_CRUD.get_all_groups_owned_by_user(do_dummy_user.id) == []

    # create some groups
    do_group_1 = GROUP_CRUD.create_group(
        schemas.GroupCreateDO(
            name="test_group_1", description="description blablablab ..."
        ),
        user_id=do_dummy_user.id,
    )
    do_group_2 = GROUP_CRUD.create_group(
        schemas.GroupCreateDO(
            name="test_group_2", description="description blablablab ..."
        ),
        user_id=do_dummy_user.id,
    )

    do_groups = GROUP_CRUD.get_all_groups_owned_by_user(do_dummy_user.id)
    assert do_group_1 == do_groups[0]
    assert do_group_2 == do_groups[1]

    # release resources
    GROUP_CRUD.delete_group(do_group_1.id)
    GROUP_CRUD.delete_group(do_group_2.id)

    return


@pytest.mark.parametrize(
    "do_dummy_user_list,do_dummy_group_list",
    [(1, 2)],
    indirect=["do_dummy_user_list", "do_dummy_group_list"],
)
def test_get_all_group_viewable_by_user(
    do_dummy_user_list: List[user_schemas.UserDO],
    do_dummy_group_list: List[schemas.GroupDO],
) -> None:
    # get a random user
    assert GROUP_CRUD.get_all_group_viewable_by_user(666666) == []

    # use dummy users and group to construct the test cases
    GROUP_CRUD.add_group_member(
        do_dummy_group_list[0].id, do_dummy_user_list[0].id
    )
    GROUP_CRUD.add_group_member(
        do_dummy_group_list[1].id, do_dummy_user_list[0].id
    )

    viewable_group_l = GROUP_CRUD.get_all_group_viewable_by_user(
        do_dummy_user_list[0].id
    )
    assert len(viewable_group_l) == 2
    for viewable_group, dummy_group in zip(
        viewable_group_l, do_dummy_group_list
    ):
        assert viewable_group.id == dummy_group.id

    # release resources
    GROUP_CRUD.delete_group_member(
        do_dummy_group_list[0].id, do_dummy_user_list[0].id
    )
    GROUP_CRUD.delete_group_member(
        do_dummy_group_list[1].id, do_dummy_user_list[0].id
    )

    return


def test_create_group(do_dummy_user: user_schemas.UserDO) -> None:
    group_create = schemas.GroupCreateDO(
        name="test_group", description="description blablablab ..."
    )

    # create a group with a random user id which is not in the user table
    # a exception should be raise
    dummy_user_id = 123456
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.create_group(group_create, user_id=dummy_user_id)
    assert (
        exc_info.type
        == EXCEPTION_LIB.GROUP__GROUP_OWNER_ID_NOT_IN_USER_TABLE.value
    )

    # create a group and do the sanity check
    do_group = GROUP_CRUD.create_group(group_create, user_id=do_dummy_user.id)
    assert do_group.name == group_create.name
    assert do_group.description == group_create.description

    # release the resource
    GROUP_CRUD.delete_group(do_group.id)

    return


def test_update_group(do_dummy_user: user_schemas.UserDO) -> None:
    group_update = schemas.GroupUpdateDO(
        name="group_updated", description="description"
    )
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.update_group(123456, group_update)
    assert exc_info.type == EXCEPTION_LIB.GROUP__GROUP_ID_NOT_EXIST.value

    do_group = GROUP_CRUD.create_group(
        schemas.GroupCreateDO(
            name="test_group_1", description="description blablablab ..."
        ),
        user_id=do_dummy_user.id,
    )
    GROUP_CRUD.delete_group(do_group.id)

    return


@pytest.mark.parametrize(
    "do_dummy_user_list", [2], indirect=["do_dummy_user_list"]
)
def test_delete_group(
    do_dummy_user: user_schemas.UserDO,
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    # delete a random group_id
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.delete_group(999999999)
    assert exc_info.type == EXCEPTION_LIB.GROUP__GROUP_ID_NOT_EXIST.value

    # Create a new group
    group_create = schemas.GroupCreateDO(
        name="test_group", description="description blablablab ..."
    )

    do_group = GROUP_CRUD.create_group(group_create, user_id=do_dummy_user.id)

    do_group_get = GROUP_CRUD.get_group(do_group.id)
    assert do_group_get is not None

    # add some members in group_members table
    GROUP_CRUD.add_group_member(do_group.id, do_dummy_user_list[0].id)
    GROUP_CRUD.add_group_member(do_group.id, do_dummy_user_list[1].id)

    # if we delete the group now, we should have integrity error since there are still members in group
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.delete_group(do_group.id)
    assert (
        exc_info.type
        == EXCEPTION_LIB.GROUP__GROUP_STILL_USED_BY_OTHER_TABLES.value
    )

    # we delete the members in group
    GROUP_CRUD.delete_group_member(do_group.id, do_dummy_user_list[0].id)
    GROUP_CRUD.delete_group_member(do_group.id, do_dummy_user_list[1].id)

    # delete, get group should be None
    GROUP_CRUD.delete_group(do_group.id)
    assert GROUP_CRUD.get_group(do_group.id) is None

    return


def test_add_delete_group_member(
    do_dummy_user: user_schemas.UserDO, do_dummy_group: schemas.GroupDO
) -> None:
    # add group member with random group id and user id
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.add_group_member(123456, 888888)
    assert (
        exc_info.type
        == EXCEPTION_LIB.GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_INTEGRITY_ERROR.value
    )

    # add group member with random user id
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.add_group_member(do_dummy_group.id, 888888)
    assert (
        exc_info.type
        == EXCEPTION_LIB.GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_INTEGRITY_ERROR.value
    )

    # add group member with random user id
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.add_group_member(123456, do_dummy_user.id)
    assert (
        exc_info.type
        == EXCEPTION_LIB.GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_INTEGRITY_ERROR.value
    )

    # delete group member with random group id and user id
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.delete_group_member(123456, 888888)
    assert (
        exc_info.type
        == EXCEPTION_LIB.GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_NOT_EXIST.value
    )

    # delete group member with random user id
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.delete_group_member(do_dummy_group.id, 888888)
    assert (
        exc_info.type
        == EXCEPTION_LIB.GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_NOT_EXIST.value
    )

    # delete group member with random user id
    with pytest.raises(Exception) as exc_info:
        _ = GROUP_CRUD.delete_group_member(123456, do_dummy_user.id)
    assert (
        exc_info.type
        == EXCEPTION_LIB.GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_NOT_EXIST.value
    )

    # add group member with a valid group id and member id
    GROUP_CRUD.add_group_member(do_dummy_group.id, do_dummy_user.id)
    GROUP_CRUD.delete_group_member(do_dummy_group.id, do_dummy_user.id)

    return


@pytest.mark.parametrize(
    "do_dummy_user_list", [2], indirect=["do_dummy_user_list"]
)
def test_get_group_members(
    do_dummy_user_list: List[user_schemas.UserDO],
    do_dummy_group: schemas.GroupDO,
) -> None:
    # get group member by a random group id
    result = GROUP_CRUD.get_group_members(888888)
    assert result.group_id == 888888
    assert result.members == []

    # use dummy users and group to construct the test cases
    for member in do_dummy_user_list:
        GROUP_CRUD.add_group_member(do_dummy_group.id, member.id)

    do_group_members = GROUP_CRUD.get_group_members(do_dummy_group.id)

    assert do_group_members.group_id == do_dummy_group.id
    assert len(do_group_members.members) == 2
    assert do_group_members.members[0] == do_dummy_user_list[0].id
    assert do_group_members.members[1] == do_dummy_user_list[1].id

    for member in do_dummy_user_list:
        GROUP_CRUD.delete_group_member(do_dummy_group.id, member.id)

    return


@pytest.mark.parametrize(
    "do_dummy_group_list",
    [2],
    indirect=["do_dummy_group_list"],
)
def test_get_group_by_ids(
    do_dummy_group_list: List[schemas.GroupDO],
) -> None:
    group_ids = [g.id for g in do_dummy_group_list]
    do_groups = GROUP_CRUD.get_group_by_ids(group_ids)
    do_group_ids = [g.id for g in do_groups]

    assert group_ids == do_group_ids

    return
