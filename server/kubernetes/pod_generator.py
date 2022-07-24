from typing import Optional, Union

from kubernetes.client import models as k8s

from server.core.exception import EXCEPTION_LIB
from server.kubernetes.base_generator import BaseGenerator

MAX_LABEL_LEN = 63


class PodGenerator(BaseGenerator):
    """
    Contains Kubernetes Airflow Worker configuration logic
    Represents a kubernetes pod and manages execution of a single pod.
    Any configuration that is container specific gets applied to
    the first container in the list of containers.
    :param pod: The fully specified pod. Mutually exclusive with `path_or_string`
    :type pod: Optional[kubernetes.client.models.V1Pod]
    :param pod_template_file: Path to YAML file. Mutually exclusive with `pod`
    :type pod_template_file: Optional[str]
    :param extract_xcom: Whether to bring up a container for xcom
    :type extract_xcom: bool
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        pod: Optional[k8s.V1Pod] = None,
        pod_template_file: Optional[str] = None,
    ) -> None:
        if not pod_template_file and not pod:
            raise EXCEPTION_LIB.KUBERNETES__CONFIG_ERROR.value(
                "Podgenerator requires either a `pod` or a `pod_template_file` argument"
            )

        if pod_template_file and pod:
            raise EXCEPTION_LIB.KUBERNETES__CONFIG_ERROR.value(
                "Cannot pass both `pod` and `pod_template_file` arguments"
            )

        if pod_template_file:
            self.ud_pod = self.deserialize_model_file(pod_template_file, "pod")
        else:
            self.ud_pod = pod

    def gen_pod(self, pod_name: str, app_name: str) -> k8s.V1Pod:
        """Generates pod"""
        result = self.ud_pod

        result.metadata.name = pod_name
        result.metadata.labels = {"app": app_name}
        return result

    # def gen_pod(self, unique_pod_name: str = None) -> k8s.V1Pod:
    #     """Generates pod"""
    #     result = self.ud_pod
    #     result.metadata.name = self.make_unique_k8s_workload_id(
    #         result.metadata.name, unique_pod_name
    #     )

    #     return result

    @staticmethod
    def from_obj(obj: dict) -> Optional[Union[dict, k8s.V1Pod]]:
        """Converts to pod from obj"""
        if obj is None:
            return None

        k8s_object = obj.get("pod_override", None)

        if isinstance(k8s_object, k8s.V1Pod):
            return k8s_object
        else:
            raise TypeError(
                "Cannot convert a non-kubernetes.client.models.V1Pod object into a KubernetesExecutorConfig"
            )
