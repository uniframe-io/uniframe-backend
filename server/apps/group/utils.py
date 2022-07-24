from server.apps.group.crud import GROUP_CRUD
from server.apps.group.schemas import GroupDO


def is_group_active(do_group: GroupDO) -> bool:
    return do_group.is_active


def is_user_group_owner(do_group: GroupDO, user_id: int) -> bool:
    return do_group.owner_id == user_id


def is_user_group_viewer(group_id: int, user_id: int) -> bool:
    do_group_members = GROUP_CRUD.get_group_members(group_id)

    if do_group_members is None:
        return False

    return user_id in do_group_members.members
