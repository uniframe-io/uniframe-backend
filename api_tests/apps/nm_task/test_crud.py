import pytest

from server.apps.nm_task import schemas
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.user import schemas as user_schemas
from server.core.exception import EXCEPTION_LIB


def test_delete_task_by_owner(
    do_dummy_user: user_schemas.UserDO,
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:

    batch_task_create = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH,
        name="dummy_batch_task",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgBatchSchema(**do_nm_batch_task_cfg_dict),
    )

    batch_task = NM_TASK_CRUD.create_task(
        batch_task_create, user_id=do_dummy_user.id
    )

    rt_task_create = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy_realtime_task",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )

    rt_task = NM_TASK_CRUD.create_task(rt_task_create, user_id=do_dummy_user.id)

    all_tasks = NM_TASK_CRUD.get_all_tasks_by_owner(do_dummy_user.id)

    assert len(all_tasks) == 2

    NM_TASK_CRUD.delete_task_by_owner(do_dummy_user.id)

    all_tasks = NM_TASK_CRUD.get_all_tasks_by_owner(do_dummy_user.id)

    assert len(all_tasks) == 0

    NM_TASK_CRUD.delete_task(batch_task.id)
    NM_TASK_CRUD.delete_task(rt_task.id)


def test_get_all_tasks_by_owner(
    do_dummy_user: user_schemas.UserDO,
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:
    assert NM_TASK_CRUD.get_task(9999999) is None

    batch_task_create = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH,
        name="dummy_batch_task",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgBatchSchema(**do_nm_batch_task_cfg_dict),
    )

    batch_task = NM_TASK_CRUD.create_task(
        batch_task_create, user_id=do_dummy_user.id
    )

    rt_task_create = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy_realtime_task",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )

    rt_task = NM_TASK_CRUD.create_task(rt_task_create, user_id=do_dummy_user.id)

    all_tasks = NM_TASK_CRUD.get_all_tasks_by_owner(do_dummy_user.id)

    assert len(all_tasks) == 2

    NM_TASK_CRUD.delete_task(batch_task.id)
    NM_TASK_CRUD.delete_task(rt_task.id)


def test_get_task(
    do_dummy_user: user_schemas.UserDO,
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:
    assert NM_TASK_CRUD.get_task(9999999) is None

    task_create = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH,
        name="dummy_batch_task",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgBatchSchema(**do_nm_batch_task_cfg_dict),
    )

    # create a group, and check if we can get it
    do_task = NM_TASK_CRUD.create_task(task_create, user_id=do_dummy_user.id)

    do_task_get = NM_TASK_CRUD.get_task(do_task.id)
    assert do_task_get == do_task

    # release the resource
    NM_TASK_CRUD.delete_task(do_task.id)

    # should be no difference for real-time task
    task_create = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy_realtime_task",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )

    # create a group, and check if we can get it
    do_task = NM_TASK_CRUD.create_task(task_create, user_id=do_dummy_user.id)

    do_task_get = NM_TASK_CRUD.get_task(do_task.id)
    assert do_task_get == do_task

    # release the resource
    NM_TASK_CRUD.delete_task(do_task.id)


def test_get_all_tasks_owned_by_user(
    do_dummy_user: user_schemas.UserDO,
    do_nm_batch_task_small_set: schemas.NmTaskDO,
    do_nm_rt_task_small_set: schemas.NmTaskDO,
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:
    # if the user_id doesn't exist, it should return None
    assert (
        NM_TASK_CRUD.get_tasks_by_owner(
            999999999, schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME
        )
        == []
    )
    assert (
        NM_TASK_CRUD.get_tasks_by_owner(
            999999999, schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH
        )
        == []
    )

    # get tasks of dummy user
    # since we have created two dummy tasks in conftest.py, we should get one group
    do_tasks = NM_TASK_CRUD.get_tasks_by_owner(
        do_dummy_user.id, schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME
    )
    assert len(do_tasks) == 1
    do_tasks = NM_TASK_CRUD.get_tasks_by_owner(
        do_dummy_user.id, schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH
    )
    assert len(do_tasks) == 1

    # create some tasks
    task_create_dummy_3 = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy_realtime_task_3",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )

    do_task_dummy_3 = NM_TASK_CRUD.create_task(
        task_create_dummy_3, user_id=do_dummy_user.id
    )

    task_create_dummy_4 = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH,
        name="dummy_realtime_task_4",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgBatchSchema(**do_nm_batch_task_cfg_dict),
    )
    do_task_dummy_4 = NM_TASK_CRUD.create_task(
        task_create_dummy_4, user_id=do_dummy_user.id
    )

    do_tasks = NM_TASK_CRUD.get_tasks_by_owner(
        do_dummy_user.id, schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH
    )
    assert len(do_tasks) == 2
    do_tasks = NM_TASK_CRUD.get_tasks_by_owner(
        do_dummy_user.id, schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME
    )
    assert len(do_tasks) == 2

    # release resources
    NM_TASK_CRUD.delete_task(do_task_dummy_3.id)
    NM_TASK_CRUD.delete_task(do_task_dummy_4.id)

    return


def test_create_task(
    do_dummy_user: user_schemas.UserDO,
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:
    # should be no difference for real-time task
    task_create = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy_realtime_task",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )

    # create a group with a random user id which is not in the user table
    # a exception should be raise
    dummy_user_id_not_exist = 123456
    with pytest.raises(Exception) as exc_info:
        _ = NM_TASK_CRUD.create_task(
            task_create, user_id=dummy_user_id_not_exist
        )
    assert (
        exc_info.type
        == EXCEPTION_LIB.TASK__TASK_OWNER_ID_NOT_IN_USER_TABLE.value
    )

    # create a group and do the sanity check
    do_task = NM_TASK_CRUD.create_task(task_create, user_id=do_dummy_user.id)
    assert do_task.name == task_create.name
    assert do_task.description == task_create.description

    # release the resource
    NM_TASK_CRUD.delete_task(do_task.id)

    return


def test_delete_task(
    do_dummy_user: user_schemas.UserDO,
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:
    # delete a random group_id
    with pytest.raises(Exception) as exc_info:
        _ = NM_TASK_CRUD.delete_task(999999999)
    assert exc_info.type == EXCEPTION_LIB.Task__Task_ID_NOT_EXIST.value

    # create tasks and delete
    task_create_dummy_3 = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy_realtime_task_3",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )

    do_task_dummy_3 = NM_TASK_CRUD.create_task(
        task_create_dummy_3, user_id=do_dummy_user.id
    )

    task_create_dummy_4 = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH,
        name="dummy_realtime_task_4",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgBatchSchema(**do_nm_batch_task_cfg_dict),
    )
    do_task_dummy_4 = NM_TASK_CRUD.create_task(
        task_create_dummy_4, user_id=do_dummy_user.id
    )

    # delete, get group should be None
    NM_TASK_CRUD.delete_task(do_task_dummy_3.id)
    assert NM_TASK_CRUD.get_task(do_task_dummy_3.id) is None

    NM_TASK_CRUD.delete_task(do_task_dummy_4.id)
    assert NM_TASK_CRUD.get_task(do_task_dummy_4.id) is None

    return


def test_get_owner_id_by_task_id(
    do_dummy_user: user_schemas.UserDO,
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:
    task_create = schemas.NmTaskCreateDO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy_realtime_task",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )
    do_task = NM_TASK_CRUD.create_task(task_create, user_id=do_dummy_user.id)
    task_id = do_task.id
    assert NM_TASK_CRUD.get_owner_id_by_task_id(task_id) == do_dummy_user.id

    NM_TASK_CRUD.delete_task(do_task.id)
