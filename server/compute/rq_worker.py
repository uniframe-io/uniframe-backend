import datetime
import os
import signal
import subprocess
import sys
import time
from typing import List, Tuple

import psutil
import redis
import rq
from fastapi import FastAPI
from pydantic.datetime_parse import parse_duration

from server.apps.nm_task.crud import NM_TASK_CRUD, NmTaskCrudAbsFactory
from server.apps.nm_task.schemas import NM_STATUS, POD_STATUS
from server.compute.utils import change_task_status, gen_pubsub_channel_name
from server.core.exception import EXCEPTION_LIB
from server.kubernetes.k8s_command import K8SCommand
from server.libs.db.sqlalchemy import (
    DBSessionMiddleware,
    db,
    engine,
    session_args,
)
from server.settings import API_SETTING
from server.settings.logger import compute_logger as logger
from server.utils.k8s_resource_name import gen_k8s_resource_prefix

app = FastAPI()
app.add_middleware(
    DBSessionMiddleware, custom_engine=engine, session_args=session_args
)


if os.getenv("API_RUN_LOCATION") in ["k8s", "minikube"]:
    worker_location = "K8S-Pod"
    k8s_command = K8SCommand()
    IN_K8S = True
    redis_conn = redis.Redis(
        host=API_SETTING.REDIS_DNS,
        port=6379,
        password=os.getenv("K8S_REDIS_PASSWORD"),
    )
    p = redis_conn.pubsub()
else:
    worker_location = "RQ-Worker"
    IN_K8S = False


def terminate_nm_task(pid: int) -> None:
    if not psutil.pid_exists(pid):
        logger.error(
            f"[{worker_location}] pid {pid} does NOT exist, subprocess ends."
        )
        return
    try:
        os.kill(pid, signal.SIGTERM)
        logger.info(f"[{worker_location}] Subprocess {pid} was killed")

    except (psutil.NoSuchProcess, psutil.ProcessLookupError):
        logger.error(
            f"[{worker_location}] psutil.NoSuchProcess, psutil.ProcessLookupError"
        )
        return


def change_task_run_table_record(
    user_id: int, task_id: int, pod_name: str, pod_status: POD_STATUS
) -> None:
    """
    change the record of AbcXyzTaskRunHistory
    """
    logger.info(
        f"[{worker_location}] change task run table record to completed"
    )
    NM_TASK_CRUD.update_task_run_record(
        user_id,
        task_id,
        pod_name,
        pod_status,
        finished_at=datetime.datetime.utcnow(),
    )


def action_stop_worker_by_command(pid: int, task_id: int) -> None:
    """
    Action when receive nm task stop command by user via backend
    Terminate the nm subprocess, K8S service if in K8S, and change task status
    """
    logger.info(
        f"[{worker_location}] Receive stop signal. Stopped by master command"
    )
    terminate_nm_task(pid=pid)
    change_task_status(
        task_id,
        NM_STATUS.STOPPED,
        f"{worker_location} proc",
        finished_at=datetime.datetime.utcnow(),
    )
    logger.info(
        f"[{worker_location}] change nm task {task_id} status to STOPPED"
    )


def action_stop_worker_by_ttl(pid: int, task_id: int) -> None:
    """
    Action when TTL is exceed and terminated
    Terminate the nm subprocess, K8S service if in K8S, and change task status
    """
    logger.info(f"[{worker_location}] TTL expired. Kill nm subprocess")
    terminate_nm_task(pid=pid)

    change_task_status(
        task_id,
        NM_STATUS.TERMINATED,
        f"{worker_location} proc",
        finished_at=datetime.datetime.utcnow(),
    )
    logger.info(
        f"[{worker_location}] change nm task {task_id} status to TERMINATED"
    )


def action_task_succeed(pid: int, task_id: int) -> None:
    """
    Action when nm task finished successfully
    logging and change task status
    """
    logger.info(f"[{worker_location}] subprocess {pid} finished successfully")

    change_task_status(
        task_id,
        NM_STATUS.COMPLETE,
        f"{worker_location} proc",
        finished_at=datetime.datetime.utcnow(),
    )
    logger.info(
        f"[{worker_location}] change nm task {task_id} status to TERMINATED"
    )


def action_task_failed(
    pid: int, task_id: int, final_status: NM_STATUS = NM_STATUS.FAILED
) -> None:
    """
    Action when nm task failed
    logging and change task status
    """
    logger.info(f"[{worker_location}] subprocess {pid} failed")

    change_task_status(
        task_id,
        final_status,
        f"{worker_location} proc",
        finished_at=datetime.datetime.utcnow(),
    )
    logger.info(
        f"[{worker_location}] change nm task {task_id} status to FAILED"
    )


def run_task_in_subprocess(
    input_para: Tuple[int, int, NmTaskCrudAbsFactory, List]
) -> None:
    """
    Spin up nm task by python popen subprocess

    In ECS and docker-compose mode, this function is triggered by RQ
    In K8S and minikube mode, this function is trigger by main function
    """

    logger.info(f"[{worker_location}] start!!!")

    # only in ECS or docker compose mode, RQ is used
    if not IN_K8S:
        rq_job: rq.job.Job = rq.get_current_job()

    task_id, user_id, task_crud, command = input_para

    with db():
        task_do = task_crud.get_task(task_id)
        if task_do is None:
            logger.error(
                f"EXECUTOR__TASK_SUBPROCESSOR_STAR_ERR: Input task id {task_id} does not exist! API_RUN_LOCATION [{os.getenv('API_RUN_LOCATION')}]"
            )
            raise EXCEPTION_LIB.EXECUTOR__TASK_SUBPROCESSOR_STAR_ERR.value(
                f"Input task id {task_id} does not exist!"
            )

        try:
            change_task_status(
                task_id,
                NM_STATUS.LAUNCHING,
                f"{worker_location} proc",
            )

            logger.info(f"[{worker_location}] kick off an nm subprocess")

            # nm realtime task needs to get nm task id from environment variables
            my_env = os.environ.copy()
            my_env["NM_TASK_ID"] = str(task_id)
            my_env["USER_ID"] = str(user_id)

            task_proc = subprocess.Popen(
                command,
                stderr=subprocess.STDOUT,
                close_fds=True,
                env=my_env,
            )
        except subprocess.CalledProcessError:
            logger.error(
                f"f[{worker_location}] EXECUTOR__TASK_SUBPROCESSOR_STAR_ERR: subprocess.Popen error:\ntask_do [{task_do}]\ncommand [{command}]"
            )
            raise EXCEPTION_LIB.EXECUTOR__TASK_SUBPROCESSOR_STAR_ERR.value(
                f"subprocess.Popen error:\ntask_do [{task_do}]\ncommand [{command}]"
            )

        process_id = task_proc.pid
        logger.info(f"[{worker_location}] pid [{process_id}]")

        if IN_K8S:
            # K8S uses redis pubsub to receive stop message
            p.subscribe(gen_pubsub_channel_name(task_id, user_id))

            # get the pod name of this worker on K8S
            app_name = gen_k8s_resource_prefix(task_id=task_id, user_id=user_id)

            # get pod name
            pod_name = os.getenv("POD_NAME")
            if pod_name is None:
                logger.error(
                    "EXECUTOR__POD_NAME_NOT_AVAILABLE: Env POD_NAME not set!"
                )
                raise EXCEPTION_LIB.EXECUTOR__POD_NAME_NOT_AVAILABLE.value(
                    "backend doesn't set pod name. Please contact administrator"
                )

        while True:
            # receive termination signal from user via backend
            if IN_K8S:
                # in K8S (EKS, minikube), pod is delete by backend

                termination_flag = p.get_message()
                if termination_flag:
                    # first message is subscription succeed
                    # {'pattern': None, 'type': 'subscribe', 'channel': 'codehole', 'data': 1L}
                    # only when type is message means a valid message
                    if termination_flag["type"] == "message":
                        # N.B. kubernete service attached to this pod should be deleted by backend
                        k8s_command.delete_nm_task_service(app_name)
                        action_stop_worker_by_command(
                            pid=task_proc.pid, task_id=task_id
                        )
                        change_task_run_table_record(
                            user_id, task_id, pod_name, POD_STATUS.COMPLETED  # type: ignore
                        )
                        break
            else:
                # only in ECS or docker compose mode, rq is used for receiving task stop message
                termination_flag = rq_job.connection.get(
                    rq_job.key + b":should_stop"
                )

                # logger.info(f"[{worker_location}] termination_flag is [{termination_flag}]")
                if termination_flag == b"1":
                    action_stop_worker_by_command(
                        pid=task_proc.pid, task_id=task_id
                    )

                    # set up the termination flag back to 0!!!
                    rq_job.connection.set(rq_job.key + b":should_stop", 0)
                    logger.info(
                        "[{worker_location}] Reset stop signal back to 0"
                    )
                    break

            # if worker is not stopped by TTL or user stop action, check task status
            task_status = task_proc.poll()

            # when task is still running
            if task_status is None:
                # if TTL expired enable
                if task_do.ext_info.running_parameter.TTL_enable:
                    execution_ttl_timedelta = parse_duration(
                        task_do.ext_info.running_parameter.TTL
                    )
                    ttl = int(execution_ttl_timedelta.total_seconds())
                    current_epoc = time.time()
                    ps = psutil.Process(task_proc.pid)
                    os_create_time_utc = ps.create_time()

                    # and TTL expired
                    if current_epoc >= os_create_time_utc + ttl:
                        logger.info(
                            f"[{worker_location}] task TTL: curr_epoc [{current_epoc}] ttl [{ttl}]  os_create_time_utc [{os_create_time_utc}] "
                        )

                        if IN_K8S:
                            # delete kubernete service attached to this pod
                            k8s_command.delete_nm_task_service(app_name)
                            change_task_run_table_record(
                                user_id, task_id, pod_name, POD_STATUS.COMPLETED  # type: ignore
                            )

                        action_stop_worker_by_ttl(
                            pid=task_proc.pid, task_id=task_id
                        )
                        break
            else:
                logger.info(
                    f"[{worker_location}] subprocess finished. handle the return code: {task_status}"
                )

                # Reason we first write task status to DB:
                # when we have out-of-memory (OOM) error, the pod maybe even killed by K8S instead of complete by the logic here
                # We try our best to write the status back to db first

                # task finish successfully
                if task_status == 0:
                    action_task_succeed(pid=task_proc.pid, task_id=task_id)
                # task exit execution with failure message
                elif task_status == -9:
                    # when return code -s -9, it is memory error
                    action_task_failed(
                        pid=task_proc.pid,
                        task_id=task_id,
                        final_status=NM_STATUS.OOMKILLED,
                    )
                else:
                    action_task_failed(pid=task_proc.pid, task_id=task_id)

                if IN_K8S:
                    # when nm task finished or failed, we also delete the attached K8S services
                    # since this pod will be deleted soon
                    k8s_command.delete_nm_task_service(app_name)
                    change_task_run_table_record(
                        user_id, task_id, pod_name, POD_STATUS.COMPLETED  # type: ignore
                    )

                break

            # TODO: Do we want to implement an exponential back-off?
            time.sleep(0.05)


# N.B.: main function is used by K8S
if __name__ == "__main__":
    task_id = int(sys.argv[1])
    user_id = int(sys.argv[2])
    command = sys.argv[3:]
    logger.info(
        f"[{worker_location}] trigger pod: task_id [{task_id}] user_id [{user_id}] command[{command}]"
    )

    run_task_in_subprocess((task_id, user_id, NM_TASK_CRUD, command))
