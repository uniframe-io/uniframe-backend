from typing import List

from fastapi import APIRouter, Depends

from server.apps.dataset import utils
from server.apps.dataset.crud import DATASET_CRUD
from server.apps.dataset.schemas import (
    OWNERSHIP_TYPE,
    DatasetCreateDO,
    DatasetCreateDTO,
    DatasetDTO,
    DatasetShareDTO,
    DatasetStatDTO,
    DatasetStatTask,
    DatasetUpdateDO,
    DatasetUpdateDTO,
    PublicDatasetCreateDO,
)
from server.apps.group.crud import GROUP_CRUD
from server.apps.media.crud import MEDIA_CRUD
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schemas import NM_STATUS, AbcXyz_TYPE
from server.apps.user.schemas import UserDO
from server.core import dependency
from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING
from server.settings.logger import app_dataset_logger as logger
from server.utils.validator import validate_resource_name

router = APIRouter()


@router.post(
    "/datasets",
    summary="Create a new dataset",
    response_model=DatasetDTO,
    response_description="Created dataset",
)
def create_dataset(
    *,
    dataset_create: DatasetCreateDTO,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> DatasetDTO:
    """
    Create a new dataset by name, description and dataset file id.

    Input schema: **DatasetCreateDTO**
    - name: name of a dataset
    - desc: description
    - media_id: media id get from media upload endpoint
    """

    if not validate_resource_name(dataset_create.name):
        logger.error(
            f"[create_dataset] NAME_INVALID: dataset name [{dataset_create.name}] current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.NAME_INVALID.value(
            f"The input dataset name {dataset_create.name} is invalid. "
            f"Please use low character, alaphbet and numbers and hyper or underscore, starting with alphabet."
        )

    do_dataset = DATASET_CRUD.get_dataset_by_name(
        current_user.id, dataset_create.name
    )
    if do_dataset is not None:
        logger.error(
            f"[create_dataset] DATASET__CURRENT_DATASET_NAME_ALREADY_EXIST: "
            f"dataset name [{dataset_create.name}] current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NAME_ALREADY_EXIST.value(
            f"Dataset name {dataset_create.name} already been used. Please use another one."
        )

    do_media = MEDIA_CRUD.get_media(dataset_create.media_id)
    if do_media is None:
        logger.error(
            f"[create_dataset] MEDIA__CURRENT_MEDIA_NOT_EXIST: media id [{dataset_create.media_id}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.MEDIA__CURRENT_MEDIA_NOT_EXIST.value(
            f"Input media {dataset_create.media_id} does not exist."
        )

    if do_media.owner_id != current_user.id:
        logger.error(
            f"[create_dataset] MEDIA__CURRENT_USER_HAS_NO_PERMISSION: do media user [{do_media.owner_id}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.MEDIA__CURRENT_USER_HAS_NO_PERMISSION.value(
            f"You are not the owner of input media {dataset_create.media_id}"
        )

    do_dataset_create = DatasetCreateDO(
        name=dataset_create.name,
        description=dataset_create.description,
        media_id=dataset_create.media_id,
        owner_id=current_user.id,
    )

    do_dataset = DATASET_CRUD.create_dataset(do_dataset_create)
    dto_dataset = DATASET_CRUD.dataset_do_to_dto(do_dataset)
    dto_media = MEDIA_CRUD.media_do_to_dto(do_media)
    dto_dataset.media = dto_media
    dto_dataset.ownership_type = OWNERSHIP_TYPE.PRIVATE

    if current_user.email == API_SETTING.OPS_ACCOUNT_EMAIL:
        DATASET_CRUD.create_public_dataset(
            PublicDatasetCreateDO(dataset_id=do_dataset.id)
        )

    return dto_dataset


@router.patch(
    "/datasets/{did}",
    summary="Update an existing dataset",
    response_model=DatasetDTO,
    response_description="Created dataset",
)
def update_dataset(
    did: int,
    dataset_update: DatasetUpdateDTO,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> DatasetDTO:
    """
    Update an existing dataset including name, description. This endpoint support partial update.
    You can send data any one of the two fields or both of them.

    Input schema: **DatasetUpdateDTO**
    - name: name of a dataset
    - desc: description
    """

    if dataset_update.name is not None:
        if not validate_resource_name(dataset_update.name):
            logger.error(
                f"[update_dataset] NAME_INVALID: dataset name [{dataset_update.name}]"
                f" current_user [{current_user.id}]"
            )
            raise EXCEPTION_LIB.NAME_INVALID.value(
                f"The input dataset name {dataset_update.name} is invalid. "
                f"Please use low character, alaphbet and numbers and hyper or underscore, starting with alphabet."
            )

        do_dataset = DATASET_CRUD.get_dataset_by_name(
            current_user.id, dataset_update.name
        )
        if do_dataset is not None and do_dataset.id != did:
            logger.error(
                f"[update_dataset] DATASET__CURRENT_DATASET_NAME_ALREADY_EXIST: dataset name [{dataset_update.name}]"
                f" current_user [{current_user.id}]"
            )
            raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NAME_ALREADY_EXIST.value(
                f"Dataset name {dataset_update.name} already been used. Please use another one."
            )

    do_dataset = DATASET_CRUD.get_dataset(did)
    if do_dataset is None:
        logger.error(
            f"[update_dataset] DATASET__CURRENT_DATASET_NOT_EXIST: dataset [{did}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
            f"Input dataset {did} not exist."
        )

    if do_dataset.owner_id != current_user.id:
        logger.error(
            f"[update_dataset] DATASET__CURRENT_USER_HAS_NO_PERMISSION: dataset owner [{do_dataset.owner_id}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "You are not allowed to update current dataset, because you are not the owner."
        )

    do_dataset_update = DatasetUpdateDO(**dataset_update.dict())
    do_dataset = DATASET_CRUD.update_dataset(did, do_dataset_update)
    dto_dataset = DATASET_CRUD.dataset_do_to_dto(do_dataset)
    dto_dataset.ownership_type = OWNERSHIP_TYPE.PRIVATE
    return dto_dataset


@router.get(
    "/datasets/{did}",
    summary="Get the detail of an exist dataset",
    response_model=DatasetDTO,
    response_description="Dataset detail",
)
def retrieve_dataset(
    did: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> DatasetDTO:
    """
    Retrieve dataset by id and only user with view permission or owner of the dataset be able to access.
    """
    do_dataset = DATASET_CRUD.get_dataset(did)
    if do_dataset is None:
        logger.error(
            f"[retrieve_dataset] DATASET__CURRENT_DATASET_NOT_EXIST: dataset [{did}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
            f"The input dataset id {did} does not exist."
        )

    have_access, ownership_type = utils.check_access(do_dataset, current_user)
    if not have_access:
        logger.error(
            f"[retrieve_dataset] DATASET__CURRENT_USER_HAS_NO_PERMISSION: dataset [{did}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "You are not allowed to get current dataset."
        )

    dto_dataset = DATASET_CRUD.dataset_do_to_dto(do_dataset)
    do_media = MEDIA_CRUD.get_media(do_dataset.media_id)
    dto_media = MEDIA_CRUD.media_do_to_dto(do_media)  # type: ignore
    dto_dataset.media = dto_media
    dto_dataset.ownership_type = ownership_type

    return dto_dataset


@router.get(
    "/datasets",
    summary="List all dataset which current user is owner or viewer",
    response_model=List[DatasetDTO],
    response_description="List datasets",
)
def list_dataset(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> List[DatasetDTO]:
    """
    List all dataset which current user is owner or viewer
    """
    # get datasets that current user is owner
    owned_datasets = DATASET_CRUD.get_datasets_by_owner(current_user.id)

    # get groups that current user is a member
    viewable_groups = GROUP_CRUD.get_all_group_viewable_by_user(current_user.id)

    # get groups that current user is owner
    owned_groups = GROUP_CRUD.get_all_groups_owned_by_user(current_user.id)

    group_ids = [g.id for g in viewable_groups + owned_groups]

    # get dataset ids that shared with the groups
    gorup_dataset_ids = DATASET_CRUD.get_dataset_shared_with_groups(group_ids)

    # get dataset ids that shared with current user
    user_dataset_ids = DATASET_CRUD.get_dataset_shared_with_user(
        current_user.id
    )

    # get public dataset ids
    public_datasets_ids = DATASET_CRUD.get_public_datasets()

    owned_dataset_ids = [d.id for d in owned_datasets]

    dataset_ids = list(
        set(
            gorup_dataset_ids
            + user_dataset_ids
            + owned_dataset_ids
            + public_datasets_ids
        )
    )
    datasets = DATASET_CRUD.get_dataset_by_ids(dataset_ids)

    dto_datasets = []
    for do_dataset in datasets:
        dto_dataset = DATASET_CRUD.dataset_do_to_dto(do_dataset)
        do_media = MEDIA_CRUD.get_media(do_dataset.media_id)
        dto_media = MEDIA_CRUD.media_do_to_dto(do_media)  # type: ignore
        dto_dataset.media = dto_media

        if dto_dataset.id in owned_dataset_ids:
            dto_dataset.ownership_type = OWNERSHIP_TYPE.PRIVATE
        elif dto_dataset.id in public_datasets_ids:
            dto_dataset.ownership_type = OWNERSHIP_TYPE.PUBLIC
        else:
            dto_dataset.ownership_type = OWNERSHIP_TYPE.SHARED
        dto_datasets.append(dto_dataset)

    return dto_datasets


@router.delete(
    "/datasets/{did}",
    summary="Delete an existing dataset",
    response_model=str,
    response_description="Delete message",
)
def destroy_dataset(
    did: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    """
    Delete dataset by id. Raise exception if the dataset not owned by current user.
    """
    do_dataset = DATASET_CRUD.get_dataset(did)
    if do_dataset is None:
        logger.error(
            f"[destroy_dataset] DATASET__CURRENT_DATASET_NOT_EXIST: dataset [{did}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
            f"Dataset of id {did} does not exist."
        )

    if not do_dataset.is_active:
        logger.error(
            f"[destroy_dataset] GROUP__CURRENT_DATASET_NOT_ACTIVE: dataset [{did}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.GROUP__CURRENT_DATASET_NOT_ACTIVE.value(
            f"The inpup dataset id {did} is not a valid one."
        )

    if do_dataset.owner_id != current_user.id:
        logger.error(
            f"[destroy_dataset] DATASET__CURRENT_USER_HAS_NO_PERMISSION: dataset owner [{do_dataset.owner_id}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "You are not allowed to delete current dataset, because you are not the owner."
        )

    do_tasks = NM_TASK_CRUD.get_all_tasks_by_owner(current_user.id)
    for t in do_tasks:
        is_running = t.ext_info.nm_status in (
            NM_STATUS.INIT,
            NM_STATUS.PREPARING,
            NM_STATUS.LAUNCHING,
            NM_STATUS.TERMINATING,
            NM_STATUS.READY,
        )
        if is_running and t.ext_info.gt_dataset_config.dataset_id == did:
            logger.error(
                f"[destroy_dataset] DATASET__DELETE_FAILED: dataset owner [{do_dataset.owner_id}]"
                f" current_user [{current_user.id}]"
            )
            raise EXCEPTION_LIB.DATASET__DELETE_FAILED.value(
                f"Current dataset {did} is used by task"
            )

    DATASET_CRUD.update_dataset(
        did,
        DatasetUpdateDO(
            is_active=False,
        ),
    )

    DATASET_CRUD.delete_public_dataset(did)
    return "Delete succeed"


@router.put(
    "/datasets/{did}/share",
    summary="Share dataset with group or user",
    response_model=str,
    response_description="Shared message",
)
def share_dataset(
    did: int,
    dataset_share: DatasetShareDTO,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    """
    Share dataset with group or user, this action can be accessed only current user is owner.
    """
    do_dataset = DATASET_CRUD.get_dataset(did)
    if do_dataset is None:
        logger.error(
            f"[share_dataset] DATASET__CURRENT_DATASET_NOT_EXIST: dataset [{did}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
            f"The input dataset id {did} does not exist."
        )

    if do_dataset.owner_id != current_user.id:
        logger.error(
            f"[share_dataset] DATASET__CURRENT_USER_HAS_NO_PERMISSION: dataset owner [{do_dataset.owner_id}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "You are not allowed to share current dataset, because you are not the owner."
        )

    group_ids = dataset_share.group_ids
    if group_ids:
        # get groups that the dataset is shared to
        old_group_ids = DATASET_CRUD.get_shared_groups(did)

        # get groups that the dataset should be shared to
        new_group_ids = list(set(group_ids) - set(old_group_ids))
        if new_group_ids:
            DATASET_CRUD.share_dataset_with_groups(did, new_group_ids)

        # get groups that should be removed
        remove_group_ids = list(set(old_group_ids) - set(group_ids))
        if remove_group_ids:
            DATASET_CRUD.remove_shared_groups(did, remove_group_ids)

    user_ids = dataset_share.user_ids
    if user_ids:
        # TODO the user_ids should be in a organization boundray or AD group boundray.
        # get users that the dataset is shared to
        old_user_ids = DATASET_CRUD.get_shared_users(did)

        # get users that the dataset should be shared to
        new_user_ids = list(set(user_ids) - set(old_user_ids))
        if current_user.id in new_user_ids:
            new_user_ids.remove(current_user.id)

        if new_user_ids:
            DATASET_CRUD.share_dataset_with_users(did, new_user_ids)

        # get users that should be removed
        remove_user_ids = list(set(old_user_ids) - set(user_ids))
        if remove_user_ids:
            DATASET_CRUD.remove_shared_users(did, remove_user_ids)

    return "Share succeed"


@router.get(
    "/datasets/{did}/stats",
    summary="Get statistics of the input dataset",
    response_model=DatasetStatDTO,
    response_description="Stat of dataset",
)
def retrieve_dataset_stats(
    did: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> DatasetStatDTO:
    """
    Get statistics of the input dataset.
    """
    do_dataset = DATASET_CRUD.get_dataset(did)
    if do_dataset is None:
        logger.error(
            f"[retrieve_dataset] DATASET__CURRENT_DATASET_NOT_EXIST: dataset [{did}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
            f"The input dataset id {did} does not exist."
        )

    if do_dataset.owner_id != current_user.id:
        logger.error(
            f"[get_dataset_status] DATASET__CURRENT_USER_HAS_NO_PERMISSION: dataset owner [{do_dataset.owner_id}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "You are not allowed to get the status of current dataset, because you are not the owner."
        )

    do_tasks = NM_TASK_CRUD.get_all_tasks_by_owner(current_user.id)
    used_by_tasks: List[DatasetStatTask] = []
    for t in do_tasks:
        is_running = t.ext_info.nm_status in (
            NM_STATUS.INIT,
            NM_STATUS.PREPARING,
            NM_STATUS.LAUNCHING,
            NM_STATUS.TERMINATING,
            NM_STATUS.READY,
        )
        if is_running:
            if (
                t.type == AbcXyz_TYPE.NAME_MATCHING_REALTIME
                and t.ext_info.gt_dataset_config.dataset_id == did
            ):
                used_by_tasks.append(
                    DatasetStatTask(
                        id=t.id,
                        name=t.name,
                        type=t.type,
                    )
                )
            if t.type == AbcXyz_TYPE.NAME_MATCHING_BATCH and (
                t.ext_info.gt_dataset_config.dataset_id == did
                or t.ext_info.nm_dataset_config.dataset_id == did  # type: ignore
            ):
                used_by_tasks.append(
                    DatasetStatTask(
                        id=t.id,
                        name=t.name,
                        type=t.type,
                    )
                )

    return DatasetStatDTO(
        used_by_tasks=used_by_tasks,
    )
