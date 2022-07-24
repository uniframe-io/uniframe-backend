import json
import os
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import redis
import requests
from fastapi import APIRouter, Depends, Request
from kubernetes.client.rest import ApiException

from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schema_converter import NmTaskSchemaConvert
from server.apps.nm_task.schemas import (
    NM_STATUS,
    POD_STATUS,
    AbcXyz_TYPE,
    NmTaskCreateDTO,
    NmTaskDTO,
    RTQueryRequestForRapidAPI,
    RTQueryRequst,
    RTQueryResp,
    SearchOption,
)
from server.apps.nm_task.utils import (
    auth_check,
    is_rq_worker_available,
    rt_nm_match_validate,
    task_start_validate,
    task_stop_validate,
    validate_task_cfg,
)
from server.apps.user.schemas import UserDO
from server.compute.rq_worker import run_task_in_subprocess
from server.compute.utils import (
    change_task_status,
    gen_pubsub_channel_name,
    get_q,
)
from server.core import dependency
from server.core.exception import EXCEPTION_LIB
from server.kubernetes.k8s_command import K8SCommand
from server.libs.fs.factory import FILE_STORE_FACTORY
from server.libs.log_service.aws_cloudwatch_logs import CloudWatchLogsHelper
from server.settings import API_SETTING
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_nm_task_logger as logger
from server.utils.k8s_resource_name import gen_k8s_resource_prefix
from server.utils.validator import validate_resource_name

router = APIRouter()
if os.getenv("API_RUN_LOCATION") in ["k8s", "minikube"]:
    k8s_command = K8SCommand()
    redis_conn = redis.Redis(
        host=API_SETTING.REDIS_DNS,
        port=6379,
        password=os.getenv("K8S_REDIS_PASSWORD"),
    )
    IN_K8S = True
else:
    IN_K8S = False


@router.post(
    "/tasks/nm",
    summary="Create a name matching task",
    response_model=NmTaskDTO,
    response_description="the created name matching batch task",
)
def create_nm_task(
    dto_nm_task_create: NmTaskCreateDTO,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> NmTaskDTO:
    """
    Create a name matching task
    """

    if not validate_resource_name(dto_nm_task_create.name):
        raise EXCEPTION_LIB.NAME_INVALID.value(
            f"The input task name {dto_nm_task_create.name} is invalid. "
            f"Please use low character, alaphbet and numbers and hyper or underscore, starting with alphabet."
        )

    if (
        dto_nm_task_create.type != AbcXyz_TYPE.NAME_MATCHING_BATCH
        and dto_nm_task_create.type != AbcXyz_TYPE.NAME_MATCHING_REALTIME
    ):
        logger.error(
            f"TASK__TASK_TYPE_NOT_CORRECT: user_id [{current_user.id}] task_type [{dto_nm_task_create.type}]"
        )
        raise EXCEPTION_LIB.TASK__TASK_TYPE_NOT_CORRECT.value(
            f"input nm task type is {dto_nm_task_create.type}. It should be either {AbcXyz_TYPE.NAME_MATCHING_BATCH} or {AbcXyz_TYPE.NAME_MATCHING_REALTIME}"
        )

    # check if task name duplicated
    do_tasks_owned = NM_TASK_CRUD.get_tasks_by_owner(
        current_user.id, dto_nm_task_create.type
    )
    if do_tasks_owned:
        if dto_nm_task_create.name in [t.name for t in do_tasks_owned]:
            logger.error(
                f"TASK__CURRENT_TASK_NAME_ALREADY_EXIST: user_id [{current_user.id}] task_name [{dto_nm_task_create.name}]"
            )
            raise EXCEPTION_LIB.TASK__CURRENT_TASK_NAME_ALREADY_EXIST.value(
                f"Task name {dto_nm_task_create.name} has been used by other tasks created by you. Please use another name."
            )

    # check name matching task configuratio
    validate_task_cfg(current_user, dto_nm_task_create)

    do_nm_task_create = NmTaskSchemaConvert.task_create_dto_2_do(
        dto_nm_task_create
    )

    do_nm_task = NM_TASK_CRUD.create_task(do_nm_task_create, current_user.id)

    dto_nm_task = NmTaskSchemaConvert.task_do_2_dto(do_nm_task)
    return dto_nm_task


@router.get(
    "/tasks/nm/{task_id}",
    summary="Get a name matching task configuration",
    response_model=NmTaskDTO,
    response_description="the name matching task",
)
def get_nm_task(
    task_id: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> NmTaskDTO:
    """
    Retrieve name matching task
    """
    do_task = NM_TASK_CRUD.get_task(task_id)
    if not do_task:
        logger.error(
            f"TASK__CURRENT_TASK_NOT_EXIST: The input task_id {task_id} does not exist! user_id [{current_user.id}] task_id [{task_id}]"
        )
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
            "The input task_id does not exist. Please make sure your select the correct task, or input the correct id in the RESTFUL API call."
        )

    auth_check(do_task, task_id, current_user.id)

    # if (not is_user_group_owner(do_group, current_user.id)) and (
    #     not is_user_group_viewer(group_id, current_user.id)
    # ):
    #     raise EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
    #         f"Group operation is not allowed: only the owner or viewer can get the detail of group {group_id}"
    #     )

    dto_nm_task = NmTaskSchemaConvert.task_do_2_dto(do_task)
    return dto_nm_task


@router.get(
    "/tasks/nm",
    summary="List all tasks which current user is owner or viewer",
    response_model=List[NmTaskDTO],
    response_description="List datasets",
)
def list_task(
    nm_type: AbcXyz_TYPE,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> List[NmTaskDTO]:
    """
    List all dataset which current user is owner or viewer
    """
    do_tasks = NM_TASK_CRUD.get_tasks_by_owner(current_user.id, nm_type)

    # TODO get all dataset which current user is viewer then merge the two parts

    dto_tasks = [NmTaskSchemaConvert.task_do_2_dto(d) for d in do_tasks]
    return dto_tasks


@router.delete(
    "/tasks/{task_id}",
    summary="Delete a task by task owner",
    response_model=str,
    response_description="What should i return???",
)
def delete_task(
    task_id: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    """
    Delete a group by given group id. Only the group owner allowed to do it
    """
    do_task = NM_TASK_CRUD.get_task(task_id)
    if not do_task:
        logger.error(
            f"TASK__CURRENT_TASK_NOT_EXIST: user_id [{current_user.id}] task_id [{task_id}]"
        )
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
            "The input task_id does not exist. Please make sure your select the correct task, or input the correct id in the RESTFUL API call."
        )

    auth_check(do_task, task_id, current_user.id)
    logger.info(f"NM task [{task_id}] delete: auth check passed")

    run_history_l = NM_TASK_CRUD.get_task_run_history_list(
        current_user.id, task_id
    )
    logger.info(f"NM task [{task_id}] pods: {run_history_l}")
    for run_record in run_history_l:
        try:
            k8s_command.ks_core.delete_namespaced_pod(
                name=run_record.pod_name,
                # TODO: put namespace nm into a config file
                namespace="nm",
            )
            logger.info(
                f"NM task [{task_id}] pod [{run_record.pod_name}]: delete successfully"
            )
        except ApiException as e:
            logger.error(
                f"Delete pod [{run_record.pod_name}] failed. Excepption {e}. However, we continue, since we try our best effort to delete"
            )
            logger.error(
                f"NM task [{task_id}] pod [{run_record.pod_name}]: delete failed"
            )

        # if the pod is still running, update pod status to deleted
        if run_record.pod_status == POD_STATUS.RUNNING.value:
            NM_TASK_CRUD.update_task_run_record_by_id(
                run_record.id,
                pod_status=POD_STATUS.DELETED,
                finished_at=datetime.utcnow(),
            )

    NM_TASK_CRUD.deactivate_task(
        task_id,
    )

    return "Delete succeed"


@router.post(
    "/tasks/nm/{task_id}/start",
    summary="Start a name matching task",
    response_model=str,
    response_description="if task start successfully",
)
def start_task(
    task_id: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    do_task = NM_TASK_CRUD.get_task(task_id)
    if not do_task:
        logger.error(
            f"TASK__CURRENT_TASK_NOT_EXIST: user_id [{current_user.id}] task_id [{task_id}]"
        )
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
            "The input task_id does not exist. Please make sure your select the correct task, or input the correct id in the RESTFUL API call."
        )

    # permission related validaiton
    auth_check(do_task, task_id, current_user.id)

    # call task validation
    task_start_validate(do_task, task_id, current_user)

    change_task_status(
        task_id,
        NM_STATUS.PREPARING,
        "nm start endpoint",
        started_at=datetime.utcnow(),
    )
    logger.info(f"NM task [{task_id}] status switched to PREPARING")

    if IN_K8S:
        if do_task.type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
            pod_name = k8s_command.run_task_in_k8s(
                task_id=do_task.id,
                user_id=current_user.id,
                entrypoint=[
                    "python",
                    "server/compute/rq_worker.py",
                ],  # K8S Pod command
                command=[
                    "python",
                    "server/compute/batch.py",
                    f"{do_task.id}",
                    f"{current_user.id}",
                ],  # work initial args
            )
        else:
            pod_name = k8s_command.run_task_in_k8s(
                task_id=do_task.id,
                user_id=current_user.id,
                entrypoint=[
                    "python",
                    "server/compute/rq_worker.py",
                ],  # K8S Pod command
                command=[
                    "uvicorn",
                    "server.compute.realtime:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    f"{API_SETTING.REALTIME_NM_ENDPOINT_PORT}",
                ],
            )

        # add record to task run history table
        NM_TASK_CRUD.add_task_run_record(current_user.id, do_task.id, pod_name)

        return f"start task {task_id} successfully"

    else:
        # ECS or local mode
        # call executor
        if not is_rq_worker_available(do_task):
            logger.error(
                f"EXECUTOR__TASK_WORKER_NOT_AVAILABLE: rq worker for type {do_task.type} is not avaiable! You are running in local mode, only 1 batch and 1 realtime can be run in the same time! user_id [{current_user.id}] task_id [{task_id}]"
            )
            raise EXCEPTION_LIB.EXECUTOR__TASK_WORKER_NOT_AVAILABLE.value(
                f"Computation worker for [{do_task.type}] type task is not avaiable! You are running in local mode, only 1 batch and 1 realtime can be run in the same time"
            )

        if do_task.type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
            q = get_q("nm_batch_worker")
            q.enqueue(
                run_task_in_subprocess,
                (
                    do_task.id,
                    current_user.id,
                    NM_TASK_CRUD,
                    [
                        "python",
                        "server/compute/batch.py",
                        f"{do_task.id}",
                        f"{current_user.id}",
                    ],
                ),
                job_id="nm_batch_task",
                job_timeout=-1,
            )
        else:
            q = get_q("nm_realtime_worker")
            q.enqueue(
                run_task_in_subprocess,
                (
                    do_task.id,
                    current_user.id,
                    NM_TASK_CRUD,
                    [
                        "uvicorn",
                        "server.compute.realtime:app",
                        "--host",
                        "0.0.0.0",
                        # "--reload", not use reload, otherwise we cannot clean uvicorn thoroughly
                        "--port",
                        f"{API_SETTING.REALTIME_NM_ENDPOINT_PORT}",
                    ],
                ),
                job_id="nm_realtime_task",
                job_timeout=-1,
            )

    return f"start task {task_id} successfully"


@router.post(
    "/tasks/nm/{task_id}/stop",
    summary="Terminate a name matching task",
    response_model=str,
    response_description="if task stop successful",
)
def stop_task(
    task_id: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    do_task = NM_TASK_CRUD.get_task(task_id)
    if not do_task:
        logger.error(
            f"TASK__CURRENT_TASK_NOT_EXIST: user_id [{current_user.id}] task_id [{task_id}]"
        )
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
            "The input task_id does not exist. Please make sure your select the correct task, or input the correct id in the RESTFUL API call."
        )

    # permission related validaiton
    auth_check(do_task, task_id, current_user.id)

    # call task validation
    task_stop_validate(do_task, task_id, current_user.id)

    # TODO: change update_at
    logger.info(
        f"User initiated to stop task {task_id} at {do_task.updated_at}"
    )
    # K8S Env
    if IN_K8S:
        redis_conn.publish(
            gen_pubsub_channel_name(task_id, current_user.id), "1"
        )
    # ECS and Local Env
    else:
        # call executor
        if do_task.type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
            worker_name = "nm_batch_worker"
            job_name = "nm_batch_task"
        else:
            worker_name = "nm_realtime_worker"
            job_name = "nm_realtime_task"

        q = get_q(worker_name)
        nm_job = q.fetch_job(job_name)

        # following the way of stackoverflow threads
        # https://stackoverflow.com/questions/55244729/python-rq-how-to-pass-information-from-the-caller-to-the-worker
        nm_job.connection.set(nm_job.key + b":should_stop", 1, ex=30)

    return f"Stop task {task_id} successfully"


@router.post(
    "/tasks/nm/{task_id}/match",
    summary="Match name by a real-time NM task",
    response_model=RTQueryResp,
    response_description="Real-time matching result",
)
def nm_realtime_match(
    task_id: int,
    query_request: RTQueryRequst,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> RTQueryResp:
    do_task = NM_TASK_CRUD.get_task(task_id)
    if not do_task:
        logger.error(
            f"TASK__CURRENT_TASK_NOT_EXIST: task_id [{task_id}] current_user[{current_user}]"
        )
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
            "The input task_id does not exist. Please make sure your select the correct task, or input the correct id in the RESTFUL API call."
        )

    if do_task.type != AbcXyz_TYPE.NAME_MATCHING_REALTIME:
        logger.error(
            f"TASK__TASK_TYPE_NOT_CORRECT: This endpoint only support real-time task! user_id [{current_user.id}] task_id [{task_id}] task_type [{do_task.type}]"
        )
        raise EXCEPTION_LIB.TASK__TASK_TYPE_NOT_CORRECT.value(
            "Matching in real-time is only for a name matching real-time task. Your selected task is a not a real-time task."
        )

    # permission related validaiton
    auth_check(do_task, task_id, current_user.id)

    # nm match validation
    rt_nm_match_validate(do_task, task_id, current_user, query_request)

    # update searching option
    do_task.ext_info.search_option = query_request.search_option
    do_task.updated_at = datetime.utcnow()
    NM_TASK_CRUD.update_task(task_id, do_task)

    # TODO: replace k8s namespace nm by a global value
    if IN_K8S:
        rt_task_svc_name = gen_k8s_resource_prefix(task_id, current_user.id)
        host_name = f"{rt_task_svc_name}.nm.svc"
        url = f"http://{host_name}{API_SETTING.API_V1_STR}/nm-realtime"
    else:
        url = f"http://{API_SETTING.REALTIME_NM_ENDPOINT_URL}:{API_SETTING.REALTIME_NM_ENDPOINT_PORT}{API_SETTING.API_V1_STR}/nm-realtime"

    payload = {"q": query_request.query_keys}

    try:
        r = requests.get(url, params=payload)
    except Exception:
        logger.error(
            f"TASK__STATUS_DISORDER: user_id [{current_user.id}] task_id [{task_id}] 'Running' in DB, but no corresponding pod. Check the task status"
        )
        raise EXCEPTION_LIB.TASK__STATUS_DISORDER.value(
            "This task status is not correct, and it is actually not running. Please delete the task, create and running it again."
        )

    return RTQueryResp(**r.json())


@router.get(
    "/tasks/nm/{task_id}/logs",
    summary="Get logs associated with the task",
    response_model=str,
    response_description="string representation of the list of log records",
)
def get_task_logs_by_task_id(
    task_id: int,
    sort_ascending: Optional[bool] = True,
    history_logs_period_second: int = 60 * 60 * 3,
    limit: int = 30,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    end_timestamp = int(datetime.today().timestamp())
    start_timestamp = end_timestamp - history_logs_period_second

    owner_id = NM_TASK_CRUD.get_owner_id_by_task_id(
        abcxyz_id=task_id,
    )
    if owner_id != current_user.id:
        logger.error(
            f"TASK__CURRENT_USER_HAS_NO_PERMISSION: task_id [{task_id}]"
        )
        raise EXCEPTION_LIB.TASK__CURRENT_USER_HAS_NO_PERMISSION.value(
            f"The current user id {current_user.id} doesn't have permission to read task id {task_id}"
        )

    if not owner_id:
        logger.error(f"TASK__CURRENT_TASK_NOT_EXIST: task_id [{task_id}]")
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
            "The input task_id does not exist. Please make sure your select the correct task, or input the correct id in the RESTFUL API call."
        )

    aws_log_helper = CloudWatchLogsHelper(
        sort_ascending=sort_ascending,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        limit=limit,
    )
    log_stream = f"nm-{owner_id}-{task_id}-"
    logs = aws_log_helper.get_logs_by_log_stream(
        log_group=GLOBAL_CONFIG.app_log_group, log_stream=log_stream
    )

    return json.dumps(logs)


@router.get(
    "/tasks/nm/{task_id}/download-batch-result",
    summary="Get batch name matching result download link",
    response_model=str,
    response_description="presigned download link",
)
def get_batch_task_result_download_url(
    task_id: int,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    """
    Retrieve name matching batch task download url
    """
    do_task = NM_TASK_CRUD.get_task(task_id)
    if not do_task:
        logger.error(
            f"TASK__CURRENT_TASK_NOT_EXIST: user_id [{current_user.id}] task_id [{task_id}]"
        )
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
            "The input task_id does not exist. Please make sure your select the correct task, or input the correct id in the RESTFUL API call."
        )

    auth_check(do_task, task_id, current_user.id)

    # if (not is_user_group_owner(do_group, current_user.id)) and (
    #     not is_user_group_viewer(group_id, current_user.id)
    # ):
    #     raise EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
    #         f"Group operation is not allowed: only the owner or viewer can get the detail of group {group_id}"
    #     )

    # this endpoint only for batch task
    if do_task.type != AbcXyz_TYPE.NAME_MATCHING_BATCH:
        logger.error(
            f"TASK__TASK_TYPE_NOT_CORRECT: user_id [{current_user.id}] task_id [{task_id}] task_type [{do_task.type}]"
        )
        raise EXCEPTION_LIB.TASK__TASK_TYPE_NOT_CORRECT.value(
            "This action is only for name matching batch task! The selected task is not a batch task"
        )

    # check batch task status
    if do_task.ext_info.nm_status not in [
        NM_STATUS.COMPLETE,
    ]:
        logger.error(
            f"TASK_COMPUTE__TASK_NOT_COMPLETE: user_id [{current_user.id}] task_id [{task_id}] nm_status [{do_task.ext_info.nm_status}]"
        )
        raise EXCEPTION_LIB.TASK_COMPUTE__TASK_NOT_COMPLETE.value(
            "The selected name matching batch task [{task_id}] has not complete yet. Please wait until the task status become COMPLETE, then download again"
        )

    o = urlparse(do_task.ext_info.matching_result.location)  # type: ignore
    bucket_name = o.netloc
    key_name = o.path.lstrip("/")

    # set a 600 second expired presigned url
    presigned_url = FILE_STORE_FACTORY.get_download_object_presigned_url(
        bucket_name=bucket_name,
        key_name=key_name,
        expiry_in_sec=GLOBAL_CONFIG.filestore_get_object_url_ttl,
    )

    return presigned_url


# TODO: add task sharing feature


@router.post(
    "/tasks/rapid-api/sanction-list-fuzzy-search",
    summary="Sanction name list matching for RapidAPI",
    response_model=RTQueryResp,
    response_description="Real-time matching result",
)
def rapidapi_nm_realtime_match(
    request: Request,
    query_request: RTQueryRequestForRapidAPI,
) -> RTQueryResp:
    rapidapi_proxy_secret = request.headers.get("x-rapidapi-proxy-secret")
    if rapidapi_proxy_secret != API_SETTING.X_RAPIDAPI_PROXY_SECRET:
        raise EXCEPTION_LIB.RAPIDAPI__SECRET_ERROR.value(
            f"RapidAPI secret mismatch. Input secret is {rapidapi_proxy_secret}. Please check the configuration secret"
        )

    task_id: int = 0
    if os.getenv("API_RUN_LOCATION") in ["k8s"]:
        redis_conn = redis.Redis(
            host=API_SETTING.REDIS_DNS,
            port=6379,
            password=os.getenv("K8S_REDIS_PASSWORD"),
        )
        task_id_bytes = redis_conn.get("RAPIDAPI_SANCTION_TASK_ID")

        # I test in python, and int.from_bytes seems doesn't work
        # task_id = int.from_bytes(task_id_bytes, "big")
        task_id = int(task_id_bytes.decode("utf-8"))
        logger.info(f"sanction task id [{task_id}]")

    if task_id == 0:
        raise EXCEPTION_LIB.TASK_COMPUTE__TASK_ID_NOT_CORRECT.value(
            "task id 0 error"
        )

    do_task = NM_TASK_CRUD.get_task(task_id)
    if not do_task:
        logger.error(f"TASK__CURRENT_TASK_NOT_EXIST: task_id [{task_id}]")
        raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
            "The input task_id does not exist. Please make sure your select the correct task, or input the correct id in the RESTFUL API call."
        )

    if do_task.type != AbcXyz_TYPE.NAME_MATCHING_REALTIME:
        logger.error(
            f"TASK__TASK_TYPE_NOT_CORRECT: This endpoint only support real-time task! task_id [{task_id}] task_type [{do_task.type}]"
        )
        raise EXCEPTION_LIB.TASK__TASK_TYPE_NOT_CORRECT.value(
            "Matching in real-time is only for a name matching real-time task. Your selected task is a not a real-time task."
        )

    # update searching option
    do_task.ext_info.search_option = SearchOption(
        top_n=1,
        threshold=0.25,
        selected_cols=[
            "data_source",
            "dataid",
            "entity_type",
            "program_type",
            "country",
        ],
    )
    do_task.updated_at = datetime.utcnow()
    NM_TASK_CRUD.update_task(task_id, do_task)

    # TODO: replace k8s namespace nm by a global value
    if IN_K8S:
        rt_task_svc_name = gen_k8s_resource_prefix(task_id, do_task.owner_id)
        host_name = f"{rt_task_svc_name}.nm.svc"
        url = f"http://{host_name}{API_SETTING.API_V1_STR}/nm-realtime"
    else:
        url = f"http://{API_SETTING.REALTIME_NM_ENDPOINT_URL}:{API_SETTING.REALTIME_NM_ENDPOINT_PORT}{API_SETTING.API_V1_STR}/nm-realtime"

    payload = {"q": query_request.query_keys}
    r = requests.get(url, params=payload)

    return RTQueryResp(**r.json())
