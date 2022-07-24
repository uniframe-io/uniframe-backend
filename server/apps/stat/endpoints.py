from fastapi import APIRouter, Depends

from server.apps.dataset.crud import DATASET_CRUD
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schemas import AbcXyz_TYPE
from server.apps.nm_task.utils import (
    is_nm_task_completed,
    is_nm_task_failed,
    is_nm_task_running,
)
from server.apps.stat.schemas import DatasetStat, StatDTO, TaskStat
from server.apps.user.schemas import UserDO
from server.core import dependency

router = APIRouter()


@router.get(
    "/stats",
    summary="Get summary of nm task and dataset",
    response_model=StatDTO,
    response_description="Summary of nm task and dataset",
)
def retrieve_dataset(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> StatDTO:
    """
    Get summary of nm task and dataset that belong to current user
    """

    do_datasets = DATASET_CRUD.get_datasets_by_owner(current_user.id)
    uploaded_dataset_count = len(do_datasets)

    batch_task_running_count: int = 0
    batch_task_failed_count: int = 0
    batch_task_complete_count: int = 0
    do_batch_tasks = NM_TASK_CRUD.get_tasks_by_owner(
        current_user.id, AbcXyz_TYPE.NAME_MATCHING_BATCH
    )
    for t in do_batch_tasks:
        nm_status = t.ext_info.nm_status
        if is_nm_task_running(nm_status):
            batch_task_running_count += 1
        if is_nm_task_failed(nm_status):
            batch_task_failed_count += 1
        if is_nm_task_completed(nm_status):
            batch_task_complete_count += 1

    rt_task_running_count: int = 0
    rt_task_failed_count: int = 0
    rt_task_complete_count: int = 0
    do_rt_tasks = NM_TASK_CRUD.get_tasks_by_owner(
        current_user.id, AbcXyz_TYPE.NAME_MATCHING_REALTIME
    )
    for t in do_rt_tasks:
        nm_status = t.ext_info.nm_status
        if is_nm_task_running(nm_status):
            rt_task_running_count += 1
        if is_nm_task_failed(nm_status):
            rt_task_failed_count += 1
        if is_nm_task_completed(nm_status):
            rt_task_complete_count += 1

    return StatDTO(
        created_dataset=DatasetStat(uploaded_count=uploaded_dataset_count),
        batch_task=TaskStat(
            created_count=len(do_batch_tasks),
            running_count=batch_task_running_count,
            failed_count=batch_task_failed_count,
            complete_count=batch_task_complete_count,
        ),
        realtime_task=TaskStat(
            created_count=len(do_rt_tasks),
            running_count=rt_task_running_count,
            failed_count=rt_task_failed_count,
            complete_count=rt_task_complete_count,
        ),
    )
