import json
import math
import time
from datetime import datetime
from datetime import datetime as dt
from datetime import timezone
from typing import Optional, Tuple, Union

import tenacity
from dateutil.parser import parse
from kubernetes import client, watch
from kubernetes.client.models.v1_pod import V1Pod
from kubernetes.client.rest import ApiException
from requests.exceptions import BaseHTTPError

from server.apps.nm_task.schemas import NM_STATUS
from server.core.exception import EXCEPTION_LIB
from server.kubernetes.kube_client import get_kube_client
from server.settings.logger import k8s_client_logger as logger


def should_retry_start_pod(exception: Exception) -> bool:
    """Check if an Exception indicates a transient error and warrants retrying"""
    if isinstance(exception, ApiException):
        return exception.status == 409
    return False


class PodStatus:
    """Status of the PODs"""

    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCEEDED = "succeeded"


class PodLauncher:
    """Launches PODS"""

    def __init__(
        self,
        kube_client: client.CoreV1Api = None,
        in_cluster: bool = True,
        cluster_context: Optional[str] = None,
    ) -> None:
        """
        Creates the launcher.
        :param kube_client: kubernetes client
        :param in_cluster: whether we are in cluster
        :param cluster_context: context of the cluster
        """
        super().__init__()
        self._client = kube_client or get_kube_client(
            in_cluster=in_cluster,
            cluster_context=cluster_context,
            client_api_version="CoreV1Api",
        )
        self._watch = watch.Watch()
        self.logger = logger

    def run_pod_async(self, pod: V1Pod, **kwargs: dict) -> V1Pod:
        """Runs POD asynchronously"""
        sanitized_pod = self._client.api_client.sanitize_for_serialization(pod)
        json_pod = json.dumps(sanitized_pod, indent=2)

        self.logger.debug("Pod Creation Request: \n%s", json_pod)
        try:
            resp = self._client.create_namespaced_pod(
                body=sanitized_pod, namespace=pod.metadata.namespace, **kwargs
            )
            self.logger.debug("Pod Creation Response: %s", resp)
        except Exception as e:
            self.logger.exception(
                "Exception when attempting to create Namespaced Pod: %s",
                json_pod,
            )
            raise e
        return resp

    def delete_pod(self, pod: V1Pod) -> None:
        """Deletes POD"""
        try:
            self._client.delete_namespaced_pod(
                pod.metadata.name,
                pod.metadata.namespace,
                body=client.V1DeleteOptions(),
            )
        except ApiException as e:
            # If the pod is already deleted
            if e.status != 404:
                raise

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_random_exponential(),
        reraise=True,
        retry=tenacity.retry_if_exception(should_retry_start_pod),
    )
    def start_pod(self, pod: V1Pod, startup_timeout: int = 120) -> None:
        """
        Launches the pod synchronously and waits for completion.
        :param pod:
        :param startup_timeout: Timeout for startup of the pod (if pod is pending for too long, fails task)
        :return:
        """
        resp = self.run_pod_async(pod)
        curr_time = dt.now()
        if resp.status.start_time is None:
            while self.pod_not_started(pod):
                self.logger.warning(
                    "Pod not yet started: %s", pod.metadata.name
                )
                delta = dt.now() - curr_time
                if delta.total_seconds() >= startup_timeout:
                    raise EXCEPTION_LIB.KUBERNETES__CONFIG_ERROR.value(
                        "Pod took too long to start"
                    )
                time.sleep(1)

    def monitor_pod(
        self, pod: V1Pod, get_logs: bool
    ) -> Union[NM_STATUS, Tuple[str, None]]:
        """
        Monitors a pod and returns the final state
        :param pod: pod spec that will be monitored
        :param get_logs: whether to read the logs locally
        :return:  Tuple[State, Optional[str]]
        """
        if get_logs:
            read_logs_since_sec = None
            last_log_time = None
            while True:
                logs = self.read_pod_logs(
                    pod, timestamps=True, since_seconds=read_logs_since_sec
                )
                for line in logs:
                    timestamp, message = self.parse_log_line(
                        line.decode("utf-8")  # type: ignore
                    )
                    last_log_time = parse(timestamp)
                    self.logger.info(message)
                time.sleep(1)

                if not self.base_container_is_running(pod):
                    break

                self.logger.warning(
                    "Pod %s log read interrupted", pod.metadata.name
                )
                if last_log_time:
                    delta = datetime.now(tz=timezone.utc) - last_log_time
                    # Prefer logs duplication rather than loss
                    read_logs_since_sec = math.ceil(delta.total_seconds())
        result = None
        return self._task_status(self.read_pod(pod)), result

    def parse_log_line(self, line: str) -> Tuple[str, str]:
        """
        Parse K8s log line and returns the final state
        :param line: k8s log line
        :type line: str
        :return: timestamp and log message
        :rtype: Tuple[str, str]
        """
        split_at = line.find(" ")
        if split_at == -1:
            raise Exception(
                f'Log not in "{{timestamp}} {{log}}" format. Got: {line}'
            )
        timestamp = line[:split_at]
        message = line[split_at + 1 :].rstrip()
        return timestamp, message

    def _task_status(self, event: V1Pod) -> NM_STATUS:
        self.logger.info(
            "Event: %s had an event of type %s",
            event.metadata.name,
            event.status.phase,
        )
        status = self.process_status(event.metadata.name, event.status.phase)
        return status

    def pod_not_started(self, pod: V1Pod) -> bool:
        """Tests if pod has not started"""
        state = self._task_status(self.read_pod(pod))
        return state == NM_STATUS.LAUNCHING

    def pod_is_running(self, pod: V1Pod) -> bool:
        """Tests if pod is running"""
        state = self._task_status(self.read_pod(pod))
        return state not in (
            NM_STATUS.TERMINATING,
            NM_STATUS.TERMINATED,
            NM_STATUS.FAILED,
        )

    def base_container_is_running(self, pod: V1Pod) -> bool:
        """Tests if base container is running"""
        event = self.read_pod(pod)
        status = next(
            iter(
                filter(
                    lambda s: s.name == "base", event.status.container_statuses
                )
            ),
            None,
        )
        if not status:
            return False
        return status.state.running is not None

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(),
        reraise=True,
    )
    def read_pod_logs(
        self,
        pod: V1Pod,
        tail_lines: Optional[int] = None,
        timestamps: bool = False,
        since_seconds: Optional[int] = None,
    ) -> str:
        """Reads log from the POD"""
        additional_kwargs = {}
        if since_seconds:
            additional_kwargs["since_seconds"] = since_seconds

        if tail_lines:
            additional_kwargs["tail_lines"] = tail_lines

        try:
            return self._client.read_namespaced_pod_log(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace,
                container="base",
                follow=True,
                timestamps=timestamps,
                _preload_content=False,
                **additional_kwargs,
            )
        except BaseHTTPError as e:
            raise EXCEPTION_LIB.KUBERNETES__CONFIG_ERROR.value(
                f"There was an error reading the kubernetes API: {e}"
            )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(),
        reraise=True,
    )
    def read_pod_events(self, pod: V1Pod) -> str:
        """Reads events from the POD"""
        try:
            return self._client.list_namespaced_event(
                namespace=pod.metadata.namespace,
                field_selector=f"involvedObject.name={pod.metadata.name}",
            )
        except BaseHTTPError as e:
            raise EXCEPTION_LIB.KUBERNETES__CONFIG_ERROR.value(
                f"There was an error reading the kubernetes API: {e}"
            )

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(),
        reraise=True,
    )
    def read_pod(self, pod: V1Pod) -> V1Pod:
        """Read POD information"""
        try:
            return self._client.read_namespaced_pod(
                pod.metadata.name, pod.metadata.namespace
            )
        except BaseHTTPError as e:
            raise EXCEPTION_LIB.KUBERNETES__CONFIG_ERROR.value(
                f"There was an error reading the kubernetes API: {e}"
            )

    def process_status(self, job_id: str, status: str) -> NM_STATUS:
        """Process status information for the JOB"""
        status = status.lower()
        if status == PodStatus.PENDING:
            return NM_STATUS.LAUNCHING
        elif status == PodStatus.FAILED:
            self.logger.error("Event with job id %s Failed", job_id)
            return NM_STATUS.FAILED
        elif status == PodStatus.SUCCEEDED:
            self.logger.info("Event with job id %s Succeeded", job_id)
            return NM_STATUS.TERMINATED
        elif status == PodStatus.RUNNING:
            return NM_STATUS.READY
        else:
            self.logger.error(
                "Event: Invalid state %s on job %s", status, job_id
            )
            return NM_STATUS.FAILED
