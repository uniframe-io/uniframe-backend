from typing import Optional

from kubernetes.client import models as k8s

from server.core.exception import EXCEPTION_LIB
from server.kubernetes.base_generator import BaseGenerator

MAX_LABEL_LEN = 63


class ServiceGenerator(BaseGenerator):
    """
    Contains Kubernetes Airflow Worker configuration logic
    Represents a kubernetes pod and manages execution of a single pod.
    Any configuration that is container specific gets applied to
    the first container in the list of containers.
    :param k8s_job: The fully specified Job. Mutually exclusive with `path_or_string`
    :type job: Optional[kubernetes.client.models.V1Job]
    :param k8s_job_template_file: Path to YAML file. Mutually exclusive with `k8s_job`
    :type k8s_job_template_file: Optional[str]
    """

    def __init__(
        self,
        k8s_service: Optional[k8s.V1Service] = None,
        k8s_service_template_file: Optional[str] = None,
    ):
        if not k8s_service_template_file and not k8s_service:
            raise EXCEPTION_LIB.KUBERNETES__CONFIG_ERROR.value(
                "Podgenerator requires either a `k8s_job` or a `k8s_job_template_file` argument"
            )

        if k8s_service_template_file and k8s_service:
            raise EXCEPTION_LIB.KUBERNETES__CONFIG_ERROR.value(
                "Cannot pass both `k8s_job` and `k8s_job_template_file` arguments"
            )

        if k8s_service_template_file:
            self.ud_job = self.deserialize_model_file(
                k8s_service_template_file, "service"
            )
        else:
            self.ud_job = k8s_service

    def gen_service(self, app_name: str) -> k8s.V1Service:
        """Generates service"""
        result = self.ud_job
        if app_name:
            result.metadata.name = f"{app_name}"
            result.spec.selector = {"app": app_name}
        return result
