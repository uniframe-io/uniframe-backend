import os
from datetime import datetime
from typing import List

from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schemas import NM_COMP_TYPE
from server.core.exception import EXCEPTION_LIB
from server.libs.docker.factory import ContainerRegistryFactory
from server.settings import API_SETTING, GLOBAL_LIMIT_CONFIG
from server.settings.logger import k8s_client_logger as logger

""" k8s related imports """
import sys

from kubernetes.client import models as k8s
from kubernetes.client.exceptions import ApiException

from server.kubernetes import kube_client
from server.kubernetes.pod_generator import PodGenerator
from server.kubernetes.pod_launcher import PodLauncher
from server.kubernetes.service_generator import ServiceGenerator
from server.kubernetes.service_launcher import ServiceLauncher
from server.kubernetes.utils import gen_pod_cpu_size, gen_pod_mem_size
from server.libs.db.sqlalchemy import db
from server.utils.k8s_resource_name import gen_k8s_resource_prefix


class K8SCommand:
    def __init__(self) -> None:
        is_in_k8s_cluster = (
            True
            if os.getenv("API_RUN_LOCATION") in ["k8s", "minikube"]
            else False
        )
        # is_in_k8s_cluster = True if os.getenv("IN_K8S_CLUSTER") else False
        self.ks_core = kube_client.get_kube_client(in_cluster=is_in_k8s_cluster)

        self.nm_pod_launcher = PodLauncher(kube_client=self.ks_core)
        if os.getenv("API_RUN_LOCATION") == "minikube":
            self.pod_path = (
                os.getenv("NAME_MATCHING_HOME", sys.path[0])
                + "/server/kubernetes/task-pod-minikube.yaml"
            )
        else:
            self.pod_path = (
                os.getenv("NAME_MATCHING_HOME", sys.path[0])
                + "/server/kubernetes/task-pod-k8s.yaml"
            )
        logger.info(f"pod path: {self.pod_path}")

        self.k8s_service_launcher = ServiceLauncher(kube_client=self.ks_core)
        self.service_path = (
            os.getenv("NAME_MATCHING_HOME", sys.path[0])
            + "/server/kubernetes/task-service-k8s.yaml"
        )

        # setup env bring to nm task pod
        self.pg_host = os.getenv("POSTGRES_HOST")
        self.pg_db = os.getenv("POSTGRES_DB")
        self.pg_user = os.getenv("POSTGRES_USER")
        self.pg_password = os.getenv("POSTGRES_PASSWORD")
        self.oauth2_github_client_id = os.getenv("OAUTH2_GITHUB_CLIENT_ID")
        self.oauth2_github_client_secret = os.getenv(
            "OAUTH2_GITHUB_CLIENT_SECRET"
        )
        self.k8s_redis_password = os.getenv("K8S_REDIS_PASSWORD")

        # setup nm pod resource dictionary
        self.pod_resource_dict = GLOBAL_LIMIT_CONFIG.task_pod_cfg

    def run_task_in_k8s(
        self, task_id: int, user_id: int, entrypoint: List, command: List
    ) -> str:
        logger.info(
            f"[K8S commander] task_id [{task_id}] user_id[{user_id}] start with command [{command}]"
        )

        with db():

            # pod_detail = self.ks_core.read_namespaced_pod("nm-718012433-1600798769-20211012203445", "nm")
            # print(pod_detail)

            task_do = NM_TASK_CRUD.get_task(task_id)
            if task_do is None:
                logger.error(
                    f"EXECUTOR__TASK_SUBPROCESSOR_STAR_ERR: Input task id {task_id} does not exist! API_RUN_LOCATION [{os.getenv('API_RUN_LOCATION')}]"
                )
                raise EXCEPTION_LIB.EXECUTOR__TASK_SUBPROCESSOR_STAR_ERR.value(
                    f"Input task id {task_id} does not exist!"
                )

            try:
                logger.info("[K8S commander] kick off an nm computation")
                """ create K8S pod """

                """k8s pod"""
                app_name = gen_k8s_resource_prefix(
                    task_id=task_id, user_id=user_id
                )
                now_str = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                pod_name = f"{app_name}-{now_str}"

                base_pod = PodGenerator(
                    pod_template_file=self.pod_path
                ).gen_pod(pod_name, app_name)
                base_pod.metadata.namespace = "nm"

                if os.getenv("API_RUN_LOCATION") == "minikube":
                    base_pod.spec.containers[
                        0
                    ].image = f"{os.getenv('PRODUCT_PREFIX')}-dev-backend-local:minikube"
                else:
                    CONTAINER_REG_FACTORY = (
                        ContainerRegistryFactory.make_concrete()
                    )
                    base_pod.spec.containers[
                        0
                    ].image = CONTAINER_REG_FACTORY.get_backend_container_image_url(
                        os.getenv("IMAGE_TAG", "latest")
                    )

                # assign resource limit
                computation_type = (
                    task_do.ext_info.computation_resource.computation_type
                )
                tshirt_size = (
                    task_do.ext_info.computation_resource.computation_config.resource_tshirt_size
                )

                container_mem_limit = gen_pod_mem_size(
                    self.pod_resource_dict[tshirt_size.value].mem_size
                )
                container_cpu_limit = gen_pod_cpu_size(
                    self.pod_resource_dict[tshirt_size.value].nr_cpu,
                    tshirt_size,
                )

                if computation_type == NM_COMP_TYPE.MULTI_THREAD:
                    # N.B. type of base_pod.spec.containers[0].resources is V1ResourceRequirements
                    # the definitation is in kubernetes/cliet/models/v1_resource_requirements.py

                    base_pod.spec.containers[0].resources.requests = {
                        "memory": container_mem_limit,
                        "cpu": container_cpu_limit,
                    }
                    base_pod.spec.containers[0].resources.limits = {
                        "memory": container_mem_limit,
                        "cpu": container_cpu_limit,
                    }

                else:
                    logger.error(
                        f"[K8S commander] computation type is {computation_type}. We only support multi-thread mode so far"
                    )
                    raise EXCEPTION_LIB.TASK__COMP_RESOURCE_NOT_SUPPORTED.value(
                        f"Computation type is {computation_type}. Only support multi-thread mode so far"
                    )

                # setup node-group for large node
                # N.B. This nodeSelector kv must match the CDK provisioned AutoScalingGroup!!!
                # and it only apply EKS
                if os.getenv("API_RUN_LOCATION") == "k8s":
                    if tshirt_size.value.lower() not in ["small", "medium"]:
                        base_pod.spec.node_selector = {
                            "node-pool": "nm-task-large"
                        }

                base_pod.spec.containers[0].env = [
                    # Pass API_RUN_LOCATION env into worker container
                    k8s.V1EnvVar(
                        name="API_RUN_LOCATION",
                        value=os.getenv("API_RUN_LOCATION"),
                    ),
                    # N.B. the env below are initiated by entrypoint.sh.
                    # since nm task pod doesn't run entrypoint.sh, we assign the env directly here
                    k8s.V1EnvVar(
                        name="OAUTH2_GITHUB_CLIENT_ID",
                        value=self.oauth2_github_client_id,
                    ),
                    k8s.V1EnvVar(
                        name="OAUTH2_GITHUB_CLIENT_SECRET",
                        value=self.oauth2_github_client_secret,
                    ),
                    k8s.V1EnvVar(name="POSTGRES_USER", value=self.pg_user),
                    k8s.V1EnvVar(
                        name="POSTGRES_PASSWORD", value=self.pg_password
                    ),
                    k8s.V1EnvVar(name="POSTGRES_HOST", value=self.pg_host),
                    k8s.V1EnvVar(name="POSTGRES_DB", value=self.pg_db),
                    k8s.V1EnvVar(
                        name="K8S_REDIS_PASSWORD", value=self.k8s_redis_password
                    ),
                    k8s.V1EnvVar(name="POD_NAME", value=pod_name),
                ]

                base_pod.spec.containers[0].command = entrypoint
                # also pass task id and user id into K8S job
                base_pod.spec.containers[0].args = [
                    str(task_id),
                    str(user_id),
                ] + command

                self.nm_pod_launcher.run_pod_async(base_pod)

                # -------------
                # create k8s service
                # -------------

                nm_service = ServiceGenerator(
                    k8s_service_template_file=self.service_path
                ).gen_service(app_name)
                nm_service.spec.ports[0].target_port = int(
                    API_SETTING.REALTIME_NM_ENDPOINT_PORT
                )

                self.k8s_service_launcher.put_service_async(nm_service)

                return pod_name

            except ApiException:
                logger.error(
                    f"[K8S commander] K8S control plane error:\ntask_do [{task_do}]\ncommand [{command}]"
                )
                raise EXCEPTION_LIB.EXECUTOR__K8S_STAR_ERR.value(
                    f"K8S resource start error:\ntask_do [{task_do}]\ncommand [{command}]"
                )

    def delete_nm_task_pod(self, pod_name: str, app_name: str) -> None:
        logger.info(
            f"[K8S commander] stop pod [{pod_name}] (pod name in a format of nm-pod-[user-id]-[task-id]-[task-created-time])"
        )

        base_pod = PodGenerator(pod_template_file=self.pod_path).gen_pod(
            pod_name, app_name
        )
        base_pod.metadata.namespace = "nm"
        self.nm_pod_launcher.delete_pod(base_pod)

    def delete_nm_task_service(self, app_name: str) -> None:
        logger.info(
            f"[K8S commander] stop service [{app_name}] (app name in a format of nm-[user-id]-[task-id])"
        )
        # Delete K8S service
        nm_service = ServiceGenerator(
            k8s_service_template_file=self.service_path
        ).gen_service(app_name)
        self.k8s_service_launcher.delete_service(nm_service)
