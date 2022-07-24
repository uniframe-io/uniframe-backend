import datetime
import os
import sys

import redis
import rq

from server.apps.dataset.utils import (
    str_in_dataset_col_headers,
    validate_dataset_access,
)
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schemas import (
    NM_STATUS,
    AbcXyz_TYPE,
    NmTaskCreateDTO,
    NmTaskDO,
    RTQueryRequst,
)
from server.apps.user.schemas import UserDO
from server.apps.user.utils import get_user_premium_type
from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING, USER_BASE_LIMIT_CONFIG
from server.settings.logger import app_nm_task_logger as logger
from server.utils.parser import load_yaml

batch_cfg_dict = load_yaml(
    os.getenv("NAME_MATCHING_HOME", sys.path[0])
    + "/conf/nm-task-batch-default.yaml"
)
BATCH_TASK_DEFAULT = NmTaskCreateDTO(**batch_cfg_dict)

rt_cfg_dict = load_yaml(
    os.getenv("NAME_MATCHING_HOME", sys.path[0])
    + "/conf/nm-task-rt-default.yaml"
)
RT_TASK_DEFAULT = NmTaskCreateDTO(**rt_cfg_dict)


def validate_task_cfg(user: UserDO, dto_task_create: NmTaskCreateDTO) -> bool:
    # nm task status must be init
    if dto_task_create.type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
        if dto_task_create.ext_info.nm_status != NM_STATUS.INIT:
            logger.error(
                f"NM_CFG__STATUS_NOT_VALID: the nm_status must be INIT! user_id [{user.id}] task_type [{dto_task_create.type}] nm_status [{dto_task_create.ext_info.nm_status}]"
            )
            raise EXCEPTION_LIB.NM_CFG__STATUS_NOT_VALID.value(
                "Validate name matching task configuration failed: the status of the selected task must be INIT status"
            )
    elif dto_task_create.type == AbcXyz_TYPE.NAME_MATCHING_REALTIME:
        if dto_task_create.ext_info.nm_status != NM_STATUS.INIT:
            logger.error(
                f"NM_CFG__STATUS_NOT_VALID: the nm_status must be INIT! user_id [{user.id}] task_type [{dto_task_create.type}] nm_status [{dto_task_create.ext_info.nm_status}]"
            )
            raise EXCEPTION_LIB.NM_CFG__STATUS_NOT_VALID.value(
                "Validate name matching task configuration failed: the status of the selected task must be INIT status"
            )

    # check groundtruth dataset accessibility
    gt_dataset_id = dto_task_create.ext_info.gt_dataset_config.dataset_id
    if not validate_dataset_access(user, gt_dataset_id):
        logger.error(
            f"NM_CFG__GROUND_TRUTH_DATA_ERR: either groundtruth dataset id does not exist, or the current user doesn't have the permission to the dataset! user_id [{user.id}] gt_dataset_id [{gt_dataset_id}]"
        )
        raise EXCEPTION_LIB.NM_CFG__GROUND_TRUTH_DATA_ERR.value(
            "Validate name matching task configuration failed: either groundtruth dataset id does not exist, or the current user doesn't have the permission to the dataset!"
        )

    # check search key of groundtruth set
    if not str_in_dataset_col_headers(
        gt_dataset_id, dto_task_create.ext_info.gt_dataset_config.search_key
    ):
        logger.error(
            f"NM_CFG__GROUND_TRUTH_HEADER_ERROR: groudtruth search key(s) is not in groundtruth dataset! user_id [{user.id}] gt_dataset_id [{gt_dataset_id}]"
        )
        raise EXCEPTION_LIB.NM_CFG__GROUND_TRUTH_HEADER_ERROR.value(
            "Validate name matching task configuraiton failed: groudtruth search key(s) is not in groundtruth dataset!"
        )

    # if it is a batch task, we need to check name matching set
    if dto_task_create.type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
        nm_dataset_id = dto_task_create.ext_info.nm_dataset_config.dataset_id  # type: ignore
        # check name matching dataset accessibility
        if not validate_dataset_access(user, nm_dataset_id):
            logger.error(
                f"NM_CFG__GROUND_TRUTH_DATA_ERR: either name matching dataset id does not exist, or the current user doesn't have the permission to the dataset! user_id [{user.id}] nm_dataset_id [{nm_dataset_id}]"
            )
            raise EXCEPTION_LIB.NM_CFG__GROUND_TRUTH_DATA_ERR.value(
                "Validate name matching task configuraiton failed: either name matching dataset id does not exist, or the current user doesn't have the permission to the dataset!"
            )

        # check search key of name matching set
        if not str_in_dataset_col_headers(
            nm_dataset_id, dto_task_create.ext_info.nm_dataset_config.search_key  # type: ignore
        ):
            logger.error(
                f"NM_CFG__GROUND_TRUTH_HEADER_ERROR name matching search key(s) is not in name matching dataset! user_id [{user.id}] nm_dataset_id [{nm_dataset_id}]"
            )
            raise EXCEPTION_LIB.NM_CFG__GROUND_TRUTH_HEADER_ERROR.value(
                "Validate name matching task configuraiton failed: name matching search key(s) is not in name matching dataset!"
            )

    """ base on user premium type, validate the task configuration """
    user_premium_type = get_user_premium_type(user)

    comp_resource = (
        dto_task_create.ext_info.computation_resource.computation_config.resource_tshirt_size.value
    )

    resource_allow_dict = USER_BASE_LIMIT_CONFIG[
        user_premium_type
    ].ui_permission.compute_resource_permission
    # we don't need to test comp_resource not in resource_allow_dict, since FastAPI Pydantic has already done it for us

    if not resource_allow_dict[comp_resource]:
        # check name matching computation resource
        # free user only support small computation resource

        logger.error(
            f"NM_CFG__COMPUTATION_RESOURCE_ERROR: Your user type [{user_premium_type}] can only use small type computation resource. User [{user.id}] Computation resource [{comp_resource}]"
        )
        raise EXCEPTION_LIB.NM_CFG__COMPUTATION_RESOURCE_ERROR.value(
            f"Your user type [{user_premium_type}] is does not allowed use computation type [{comp_resource}]"
        )

    """ user premium type is not allow to change TTL setting """
    # TTL check: for free user, TTL value and TTL enable flag is not editable
    if not USER_BASE_LIMIT_CONFIG[
        user_premium_type
    ].ui_permission.change_task_ttl:
        ttl_enable = dto_task_create.ext_info.running_parameter.TTL_enable
        if dto_task_create.type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
            ttl_enable_default_val = (
                BATCH_TASK_DEFAULT.ext_info.running_parameter.TTL_enable
            )
        else:
            ttl_enable_default_val = (
                RT_TASK_DEFAULT.ext_info.running_parameter.TTL_enable
            )

        ttl_value = dto_task_create.ext_info.running_parameter.TTL
        if dto_task_create.type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
            ttl_default_val = BATCH_TASK_DEFAULT.ext_info.running_parameter.TTL
        else:
            ttl_default_val = RT_TASK_DEFAULT.ext_info.running_parameter.TTL
        if ttl_value != ttl_default_val or ttl_enable != ttl_enable_default_val:
            logger.error(
                f"NM_CFG__RUNNING_PARAM_TTL_ERROR: free user can only use the default TTL value. User [{user.id}] input_ttl_value [{ttl_value}] default_ttl_value [{ttl_default_val}]"
            )
            raise EXCEPTION_LIB.NM_CFG__RUNNING_PARAM_TTL_ERROR.value(
                f"Free user is not allowed to change TTL value. Your input TTL value is [{ttl_value}]"
            )

    return True


def is_task_active(do_task: NmTaskDO) -> bool:
    return do_task.is_active


def is_user_task_owner(do_task: NmTaskDO, user_id: int) -> bool:
    return do_task.owner_id == user_id


# def is_user_group_viewer(group_id: int, user_id: int) -> bool:
#     do_group_members = GROUP_CRUD.get_group_members(group_id)

#     if do_group_members is None:
#         return False

#     return user_id in do_group_members.members


def auth_check(do_task: NmTaskDO, task_id: int, user_id: int) -> None:
    if not is_task_active(do_task):
        logger.error(
            f"TASK__CURRENT_TASK_NOT_ACTIVE: The input task_id {task_id} is not a valid one! user_id [{user_id}]"
        )
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_ACTIVE.value(
            "The select name matching task is not a active one. Has you already delete it?"
        )

    if not is_user_task_owner(do_task, user_id):
        logger.error(
            f"TASK__CURRENT_USER_HAS_NO_PERMISSION: Task operation is not allowed: the current user doesn't have the permission to the task! user_id [{user_id}] task_id [{task_id}]"
        )
        logger.error(do_task.dict())
        raise EXCEPTION_LIB.TASK__CURRENT_USER_HAS_NO_PERMISSION.value(
            "The action you did is not allowed: the current user doesn't have the permission to the task"
        )

    return


def is_nm_task_running(nm_status: NM_STATUS) -> bool:
    if nm_status in [
        NM_STATUS.PREPARING,
        NM_STATUS.LAUNCHING,
        NM_STATUS.READY,
        NM_STATUS.TERMINATING,
    ]:
        return True

    return False


def is_nm_task_failed(nm_status: NM_STATUS) -> bool:
    if nm_status in [
        NM_STATUS.FAILED,
        NM_STATUS.OOMKILLED,
    ]:
        return True

    return False


def is_nm_task_completed(nm_status: NM_STATUS) -> bool:
    if nm_status in [
        NM_STATUS.STOPPED,
        NM_STATUS.TERMINATED,
        NM_STATUS.COMPLETE,
    ]:
        return True

    return False


def task_start_validate(
    current_task: NmTaskDO, task_id: int, user: UserDO
) -> None:
    user_premium_type = get_user_premium_type(user)

    # if running task number has reach the month quota
    # N.B. current implement is actual the 30 day rolling window
    # TODO: use dateutil to get exactly 1 month delta
    # TODO: change to real calendar monthly quota, when we enable payment later
    last_month = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    logger.info(f"last month [{last_month}]")
    last_month_run_l = NM_TASK_CRUD.get_records_by_started_at(
        user.id, oldest_started_at=last_month
    )

    monthly_running_api_quota = USER_BASE_LIMIT_CONFIG[
        user_premium_type
    ].compute.max_running_api_call_per_month
    if len(last_month_run_l) >= monthly_running_api_quota:
        logger.error(
            f"TASK_COMPUTE__MONTHLY_RUN_QUOTA_REACH: The user [{user.id}] has used run task API [{len(last_month_run_l)}] times. Monthly quota reached."
        )
        raise EXCEPTION_LIB.TASK_COMPUTE__MONTHLY_RUN_QUOTA_REACH.value(
            f"You have already reached monthly task running quota [{monthly_running_api_quota}]. Please contact info@uniframe.io if you want to enlarge monthly quota."
        )

    # if the task has already been triggered, we will not trigger it again
    if is_nm_task_running(current_task.ext_info.nm_status):
        logger.error(
            f"TASK_COMPUTE__TASK_HAS_BEEN_RUNNING: The user [{user.id}] has already had task [{task_id}] running with status [{current_task.ext_info.nm_status}]"
        )
        raise EXCEPTION_LIB.TASK_COMPUTE__TASK_HAS_BEEN_RUNNING.value(
            f"Task [{current_task.name}] has already been running with status [{current_task.ext_info.nm_status}]"
        )

    # TODO: when we add nm task sharing feature (user can run other user shared task)
    # we need to change `get_all_tasks_by_owner` function to something like `get_all_task_by_viewer`
    do_task_l = NM_TASK_CRUD.get_all_tasks_by_owner(user.id)
    nr_running_task = 0
    running_task_l = []

    # different setting for different type of user
    max_running_task_nr = USER_BASE_LIMIT_CONFIG[
        user_premium_type
    ].compute.max_running_task_nr

    for do_task in do_task_l:
        if is_nm_task_running(do_task.ext_info.nm_status):
            nr_running_task += 1
            running_task_l.append(do_task.id)

        if nr_running_task >= max_running_task_nr:
            logger.error(
                f"TASK_COMPUTE__MAX_RUNNING_TASK_NR_REACH: The user [{user.id}] has already had [{nr_running_task}] running job. Running job list: [{running_task_l}]"
            )
            raise EXCEPTION_LIB.TASK_COMPUTE__MAX_RUNNING_TASK_NR_REACH.value(
                f"Free user only can run {max_running_task_nr} simultaneous job. You have already had more than {nr_running_task} job running"
            )

    return


def task_stop_validate(do_task: NmTaskDO, task_id: int, user_id: int) -> None:
    return


def rt_nm_match_validate(
    do_task: NmTaskDO, task_id: int, user: UserDO, query_request: RTQueryRequst
) -> None:
    if do_task.type != AbcXyz_TYPE.NAME_MATCHING_REALTIME:
        logger.error(
            f"NM_RT__TASK_TYPE_ERR: The input task {task_id} is not a realtime name matching task user_id [{user.id}]"
        )
        raise EXCEPTION_LIB.NM_RT__TASK_TYPE_ERR.value(
            "The selected task is not a realtime name matching task"
        )

    if do_task.ext_info.nm_status != NM_STATUS.READY:
        logger.error(
            f"NM_RT__TASK_NOT_READY: The input task {task_id} is not in a READY status! user_id [{user.id}] task_id [{task_id}]"
        )
        raise EXCEPTION_LIB.NM_RT__TASK_NOT_READY.value(
            "The selected task is not in a READY status. Only when the task is in READY status, you can do the real-time matching"
        )

    # validation: max len of the list
    user_premium_type = get_user_premium_type(user)
    if (
        len(query_request.query_keys)
        > USER_BASE_LIMIT_CONFIG[user_premium_type].compute.max_rt_nr_queries
    ):
        logger.error(
            f"NM_RT__EXCEED_MAX_RT_NR_QUERIES_LIMIT: You can query {USER_BASE_LIMIT_CONFIG[user_premium_type].compute.max_rt_nr_queries} words at most in one run! user_id [{user.id}] length query list [{len(query_request.query_keys)}] task_id [{task_id}]"
        )
        raise EXCEPTION_LIB.NM_RT__EXCEED_MAX_RT_NR_QUERIES_LIMIT.value(
            f"You can query {USER_BASE_LIMIT_CONFIG[user_premium_type].compute.max_rt_nr_queries} words at most in one run"
        )
    return


def is_rq_worker_available(do_task: NmTaskDO) -> bool:
    """
    Check if RQ worker avaialable
    ONLY USED in ECR or docker-compose mode
    """
    is_available = False
    if do_task.type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
        job_id = "nm_batch_task"
    else:
        job_id = "nm_realtime_task"

    try:
        redis_conn = redis.Redis(host=API_SETTING.REDIS_DNS, port=6379, db=0)
        rq_job = rq.job.Job.fetch(job_id, redis_conn)
    except rq.exceptions.NoSuchJobError:
        # no job run yet
        is_available = True
    else:
        rq_job_status = rq_job.get_status()
        if rq_job_status in ["finished", "stopped", "failed"]:
            is_available = True

    return is_available
