from typing import List, Optional, Set

from fastapi import APIRouter, Depends

from server.apps.dataset import utils as dataset_utils
from server.apps.dataset.crud import DATASET_CRUD
from server.apps.group.crud import GROUP_CRUD
from server.apps.group.schema_converter import GroupSchemaConvert
from server.apps.group.schemas import (
    GroupCreateDTO,
    GroupDTO,
    GroupMembersDTO,
    GroupUpdateDTO,
)
from server.apps.group.utils import (
    is_group_active,
    is_user_group_owner,
    is_user_group_viewer,
)
from server.apps.user.schemas import UserDO
from server.core import dependency
from server.core.exception import EXCEPTION_LIB
from server.settings.logger import app_group_logger as logger
from server.utils.validator import validate_resource_name

router = APIRouter()


@router.post(
    "/groups",
    summary="Create a group",
    response_model=GroupDTO,
    response_description="Created group",
)
def create_group(
    *,
    dto_group_create: GroupCreateDTO,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> GroupDTO:
    """
    Create a new group

    Input schema: **GroupCreateDTO**
    - name: group name
    - desc: group descriptions
    - members: a set of user id
    """

    if not validate_resource_name(dto_group_create.name):
        logger.error(
            "EXCEPTION_LIB.NAME_INVALID: The input group name {dto_group_create.name} is invalid."
        )
        raise EXCEPTION_LIB.NAME_INVALID.value(
            f"The input group name {dto_group_create.name} is invalid. "
            f"Please use low character, alaphbet and numbers and hyper or underscore, starting with alphabet."
        )

    do_groups_owned = GROUP_CRUD.get_all_groups_owned_by_user(current_user.id)
    # logger.info(
    #     f"The current user {current_user.id} has owned groups: {do_groups_owned}"
    # )

    if do_groups_owned:
        # logger.info(
        #     f"{dto_group_create.name}, {type(dto_group_create.name)}, {[g.name for g in do_groups_owned]}, {dto_group_create.name in [g.name for g in do_groups_owned]}"
        # )
        if dto_group_create.name in [g.name for g in do_groups_owned]:
            raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NAME_ALREADY_EXIST.value(
                f"Group name {dto_group_create.name} has been used by other groups created by you. Please use another name."
            )

    do_group_create = GroupSchemaConvert.group_create_dto_2_do(dto_group_create)
    do_group = GROUP_CRUD.create_group(do_group_create, current_user.id)

    return GroupSchemaConvert.group_do_2_dto(do_group)


def get_shared_groups(
    action: str, resource_type: str, query: int, current_user: UserDO
) -> List[GroupDTO]:
    """
    Get groups shared with dataset
    """
    if action != "shared" or resource_type != "dataset":
        return []

    if not query:
        return []

    do_dataset = DATASET_CRUD.get_dataset(query)
    if do_dataset is None:
        return []

    have_access, ownership_type = dataset_utils.check_access(
        do_dataset, current_user
    )
    if not have_access:
        raise EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "You are not allowed to get current dataset."
        )

    group_ids = DATASET_CRUD.get_shared_groups(query)

    do_groups = GROUP_CRUD.get_group_by_ids(group_ids)

    return [
        GroupSchemaConvert.group_do_2_dto(do_group) for do_group in do_groups
    ]


@router.get(
    "/groups",
    summary="Get a list of group owned or viewable by user",
    response_model=List[GroupDTO],
    response_description="list of groups owned or viewable by user",
)
def get_all_groups(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    query: Optional[int] = None,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> List[GroupDTO]:
    """
    Retrieve all groups owned or viewable by user

    1. Get all groups that current user has owner or viewer access
    2. Get groups that shared with dataset

    - action: shared
    - resource_type: dataset
    - query: dataset id
    - current_user: logged-in user
    """

    if action:
        if not resource_type or not query:
            return []
        return get_shared_groups(action, resource_type, query, current_user)

    # 1. get all groups ownder by user
    do_owned_groups = GROUP_CRUD.get_all_groups_owned_by_user(current_user.id)

    # 2. get all groups viewable by user
    # viewable_group_id_l = GROUP_CRUD.get_all_group_ids_viewable_by_user(
    #     current_user.id
    # )
    # do_viewable_groups = []
    # for group_id in viewable_group_id_l:
    #     do_group = GROUP_CRUD.get_group(group_id)
    #     if not do_group:
    #         raise EXCEPTION_LIB.GROUP__GROUP_TABLE_MEMBER_TABLE_OUT_OF_SYNC.value(
    #             f"group_id {group_id} is shared with current user, but it is not in the group table!"
    #         )
    #     do_viewable_groups.append(do_group)
    do_viewable_groups = GROUP_CRUD.get_all_group_viewable_by_user(
        current_user.id
    )

    do_groups = do_owned_groups + do_viewable_groups

    return [
        GroupSchemaConvert.group_do_2_dto(do_group) for do_group in do_groups
    ]


@router.get(
    "/groups/{group_id}",
    summary="Get detailed information of a group",
    response_model=GroupDTO,
    response_description="group details",
)
def get_group(
    group_id: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> GroupDTO:
    """
    Retrieve a group details by group id. Only the group owner allowed to do it.
    """

    do_group = GROUP_CRUD.get_group(group_id)
    if not do_group:
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_EXIST.value(
            f"The input group_id {group_id} does not exist"
        )

    if not is_group_active(do_group):
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_ACTIVE.value(
            f"The input group_id {group_id} is not a valid one"
        )

    if (not is_user_group_owner(do_group, current_user.id)) and (
        not is_user_group_viewer(group_id, current_user.id)
    ):
        raise EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
            f"Group operation is not allowed: only the owner or viewer can get the detail of group {group_id}"
        )

    return GroupSchemaConvert.group_do_2_dto(do_group)


@router.put(
    "/groups/{group_id}",
    summary="Update group information by group owner",
    response_model=GroupDTO,
    response_description="updated group details",
)
def update_group(
    group_id: int,
    group_update: GroupUpdateDTO,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> GroupDTO:
    """
    Update a group by the input group detail. Only the group owner allowed to do it
    """

    if not validate_resource_name(group_update.name):
        raise EXCEPTION_LIB.NAME_INVALID.value(
            f"The input group name {group_update.name} is invalid. "
            f"Please use low character, alaphbet and numbers and hyper or underscore, starting with alphabet."
        )

    do_group = GROUP_CRUD.get_group(group_id)
    if not do_group:
        # TODO: add log info for exception part in this file
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_EXIST.value(
            f"The input group_id {group_id} does not exist"
        )

    if not is_group_active(do_group):
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_ACTIVE.value(
            f"The input group_id {group_id} is not a valid one"
        )

    if not is_user_group_owner(do_group, current_user.id):
        raise EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
            f"Group operation is not allowed: only the owner can edit group {group_id}"
        )

    # TODO: check if updated name exisits?

    do_group_update = GroupSchemaConvert.group_update_dto_2_do(group_update)
    do_group = GROUP_CRUD.update_group(group_id, do_group_update)

    return GroupSchemaConvert.group_do_2_dto(do_group)


@router.delete(
    "/groups/{group_id}",
    summary="Delete a group by group owner",
    response_model=str,
    response_description="What should i return???",
)
def delete_group(
    group_id: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    """
    Delete a group by given group id. Only the group owner allowed to do it
    """
    do_group = GROUP_CRUD.get_group(group_id)
    if not do_group:
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_EXIST.value(
            f"The input group_id {group_id} does not exist"
        )

    if not is_group_active(do_group):
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_ACTIVE.value(
            f"The input group_id {group_id} is not a valid one"
        )

    if not is_user_group_owner(do_group, current_user.id):
        raise EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
            f"Group operation is not allowed: only the owner can delete group {group_id}"
        )

    GROUP_CRUD.delete_group(group_id)

    return "Delete succeed"


@router.get(
    "/groups/{group_id}/members",
    summary="Get all members of a group",
    response_model=GroupMembersDTO,
    response_description="A set of member id",
)
def get_group_members(
    group_id: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> GroupMembersDTO:
    """
    Get all members of a given group id.
    Only group owner or viewer is allowed for this action
    """
    do_group = GROUP_CRUD.get_group(group_id)
    if not do_group:
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_EXIST.value(
            f"The input group_id {group_id} does not exist"
        )

    if not is_group_active(do_group):
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_ACTIVE.value(
            f"The input group_id {group_id} is not a valid one"
        )

    if (not is_user_group_owner(do_group, current_user.id)) and (
        not is_user_group_viewer(group_id, current_user.id)
    ):
        raise EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
            f"Group operation is not allowed: only the owner or viewer can get the members of group {group_id}"
        )

    do_group_members = GROUP_CRUD.get_group_members(group_id)

    return GroupSchemaConvert.group_members_do_2_dto(do_group_members)


@router.post(
    "/groups/{group_id}/members",
    summary="Set members of a group",
    response_model=GroupMembersDTO,
    response_description="A set of member id",
)
def set_group_members(
    group_id: int,
    members: Set[int],
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> GroupMembersDTO:
    """
    Set members of a group
    Only group owner is allowed for this action
    """

    do_group = GROUP_CRUD.get_group(group_id)
    if not do_group:
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_EXIST.value(
            f"The input group_id {group_id} does not exist"
        )

    if not is_group_active(do_group):
        raise EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_ACTIVE.value(
            f"The input group_id {group_id} is not a valid one"
        )

    if not is_user_group_owner(do_group, current_user.id):
        raise EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
            f"Group operation is not allowed: only the owner can set the members of group {group_id}"
        )

    # 1. get the old members
    do_old_group_members = GROUP_CRUD.get_group_members(group_id)
    old_member_set = set(do_old_group_members.members)

    # 2. get the new members
    new_member_set = set(members)

    # 3. Update
    # 3.1 remove members need to be deleted
    member_rm_l = list(old_member_set - new_member_set)

    # 3.2 add new members
    member_add_l = list(new_member_set - old_member_set)

    # 3.3 update members
    do_group_members = GROUP_CRUD.update_group_members(
        group_id, member_add_l, member_rm_l
    )

    return GroupSchemaConvert.group_members_do_2_dto(do_group_members)
