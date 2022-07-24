import os
import time
from datetime import datetime

import boto3
import redis

from server.api.main import app  # noqa: F401
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schemas import NM_STATUS, POD_STATUS
from server.compute.utils import change_task_status
from server.kubernetes import kube_client
from server.libs.db.sqlalchemy import db
from server.settings import API_SETTING
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import init_logging
from server.utils.aws_helper import id_gen

logger = init_logging().getLogger("housekeeper")

if os.getenv("API_RUN_LOCATION") in ["k8s"]:
    redis_conn = redis.Redis(
        host=API_SETTING.REDIS_DNS,
        port=6379,
        password=os.getenv("K8S_REDIS_PASSWORD"),
    )
    ssm_client = boto3.client("ssm", region_name=GLOBAL_CONFIG.region.value)


def housekeeping() -> None:
    """
    This housekeeping process will do the following every 5 seconds
    1. Get the real pod status of the running nm tasks in task run history table
    2. if the pod state is terminated by OOMKilled
            - change the task running history table status
            - change the task table status

    - for running container
        {'running': {'started_at': datetime.datetime(2021, 10, 14, 13, 36, 58, tzinfo=tzlocal())},
        'terminated': None,
        'waiting': None}

    - for complete container
        {'running': None,
        'terminated': {'container_id': 'docker://609c5c65448a094bcfe2739e6a8be6298c54ac455bb94cd844f2ac9d701c6af3',
                        'exit_code': 0,
                        'finished_at': datetime.datetime(2021, 10, 14, 13, 43, 27, tzinfo=tzlocal()),
                        'message': None,
                        'reason': 'Completed',
                        'signal': None,
                        'started_at': datetime.datetime(2021, 10, 14, 13, 36, 58, tzinfo=tzlocal())},
        'waiting': None}

    - for OOMKilled container
        {'running': None,
        'terminated': {'container_id': 'docker://00949b0f71f814a25ac710465a2e1782f29b517aecf7117a3fdfa0e06af56c65',
                        'exit_code': 137,
                        'finished_at': datetime.datetime(2021, 10, 14, 13, 45, 35, tzinfo=tzlocal()),
                        'message': None,
                        'reason': 'OOMKilled',
                        'signal': None,
                        'started_at': datetime.datetime(2021, 10, 14, 13, 45, 12, tzinfo=tzlocal())},
        'waiting': None}
    """
    # This housekeeping task is only for k8s
    ks_client = kube_client.get_kube_client(in_cluster=True)

    while True:
        time.sleep(10)

        if os.getenv("API_RUN_LOCATION") in ["k8s"]:
            # update DEMO_ACCOUNT_LIMITATION
            ssm_parameter_name = id_gen("ssm-demo-account-limitation")
            demo_account_limitation = ssm_client.get_parameter(
                Name=ssm_parameter_name
            )["Parameter"]["Value"]
            redis_conn.mset(
                {"DEMO_ACCOUNT_LIMITATION": demo_account_limitation}
            )

            ssm_parameter_name = id_gen("rapidapi-sanction-task-id")
            rapidapi_sanction_task_id = ssm_client.get_parameter(
                Name=ssm_parameter_name
            )["Parameter"]["Value"]
            redis_conn.mset(
                {"RAPIDAPI_SANCTION_TASK_ID": rapidapi_sanction_task_id}
            )

        with db():
            running_task_l = NM_TASK_CRUD.get_all_running_task_pod()

            for running_task in running_task_l:
                # TODO: need a super user as task manager which can delete any tasks
                # TODO: get namespace from global configuration
                try:
                    pod_obj = ks_client.read_namespaced_pod(
                        name=running_task.pod_name, namespace="nm"
                    )
                except Exception as e:  # noqa
                    logger.info(
                        f"Pod [{running_task.pod_name}] not found! Please check the status of this pod. It is in db but not in EKS. Change status to COMPLETE",
                    )
                    NM_TASK_CRUD.update_task_run_record_by_id(
                        running_task.id,
                        POD_STATUS.COMPLETED,
                        finished_at=datetime.utcnow(),
                    )
                    continue

                # N.B. when pod is still starting, for example, during auto scaling.
                # pod is in pending status, and there is no container status
                if pod_obj.status.container_statuses is None:
                    continue

                nm_container_state = pod_obj.status.container_statuses[0].state
                if nm_container_state.terminated:
                    if nm_container_state.terminated.reason == "OOMKilled":
                        NM_TASK_CRUD.update_task_run_record_by_id(
                            running_task.id,
                            POD_STATUS.OOMKILLED,
                            finished_at=datetime.utcnow(),
                        )
                        logger.info(
                            f"change task run history id [{running_task.id}] user_id [{running_task.owner_id}] task_id [{running_task.task_id}] pod_name [{running_task.pod_name}] to OOMKilled"
                        )

                        # TODO: change finished at to pod terminated time
                        change_task_status(
                            running_task.task_id,
                            NM_STATUS.OOMKILLED,
                            "housekeeper",
                            finished_at=datetime.utcnow(),
                        )


# N.B.: main function is used by K8S
if __name__ == "__main__":
    logger.info("start housekeeping")

    housekeeping()
