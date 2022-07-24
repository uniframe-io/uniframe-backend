from typing import Optional, Tuple

from server.apps.dataset.crud import DATASET_CRUD
from server.apps.dataset.schemas import OWNERSHIP_TYPE, DatasetDO
from server.apps.group.crud import GROUP_CRUD
from server.apps.media.crud import MEDIA_CRUD
from server.apps.user.schemas import UserDO


def check_access(
    dataset: DatasetDO, user: UserDO
) -> Tuple[bool, Optional[OWNERSHIP_TYPE]]:
    if dataset.owner_id == user.id:
        return True, OWNERSHIP_TYPE.PRIVATE

    # get dataset ids that shared with current user
    user_dataset_ids = DATASET_CRUD.get_dataset_shared_with_user(user.id)
    if dataset.id in user_dataset_ids:
        return True, OWNERSHIP_TYPE.SHARED

    # get groups that the dataset is shared to
    dataset_shared_group_ids = DATASET_CRUD.get_shared_groups(dataset.id)
    for shared_group_id in dataset_shared_group_ids:
        shared_group_members = GROUP_CRUD.get_group_members(shared_group_id)

        if user.id in shared_group_members.members:
            return True, OWNERSHIP_TYPE.SHARED

    # get public datasets
    public_dataset_ids = DATASET_CRUD.get_public_datasets()
    if dataset.id in public_dataset_ids:
        return True, OWNERSHIP_TYPE.PUBLIC

    return False, None


def validate_dataset_access(user: UserDO, dataset_id: int) -> bool:
    do_dataset = DATASET_CRUD.get_dataset(dataset_id)
    if do_dataset is None:
        return False

    if not check_access(do_dataset, user)[0]:
        return False

    return True


def str_in_dataset_col_headers(dataset_id: int, col: str) -> bool:
    """
    Judge if a str is in the dataset column headers or not
    """
    do_dataset = DATASET_CRUD.get_dataset(dataset_id)
    if do_dataset is None:
        return False

    do_media = MEDIA_CRUD.get_media(do_dataset.media_id)
    if do_media is None:
        return False

    if col not in do_media.ext_info.header:
        return False

    return True
