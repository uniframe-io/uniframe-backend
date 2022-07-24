import datetime
import hashlib
import os
import re
import uuid
from typing import Optional, Union

from dateutil import parser
from kubernetes.client import models as k8s
from kubernetes.client.api_client import ApiClient

from server.utils.parser import safe_load_yaml_io

MAX_LABEL_LEN = 63


def make_safe_label_value(string: str) -> str:
    """
    Valid label values must be 63 characters or less and must be empty or begin and
    end with an alphanumeric character ([a-z0-9A-Z]) with dashes (-), underscores (_),
    dots (.), and alphanumerics between.
    If the label value is greater than 63 chars once made safe, or differs in any
    way from the original value sent to this function, then we need to truncate to
    53 chars, and append it with a unique hash.
    """
    safe_label = re.sub(
        r"^[^a-z0-9A-Z]*|[^a-zA-Z0-9_\-\.]|[^a-z0-9A-Z]*$", "", string
    )

    if len(safe_label) > MAX_LABEL_LEN or string != safe_label:
        safe_hash = hashlib.md5(string.encode()).hexdigest()[:9]
        safe_label = (
            safe_label[: MAX_LABEL_LEN - len(safe_hash) - 1] + "-" + safe_hash
        )

    return safe_label


def datetime_to_label_safe_datestring(datetime_obj: datetime.datetime) -> str:
    """
    Kubernetes doesn't like ":" in labels, since ISO datetime format uses ":" but
    not "_" let's
    replace ":" with "_"
    :param datetime_obj: datetime.datetime object
    :return: ISO-like string representing the datetime
    """
    return datetime_obj.isoformat().replace(":", "_").replace("+", "_plus_")


def label_safe_datestring_to_datetime(string: str) -> datetime.datetime:
    """
    Kubernetes doesn't permit ":" in labels. ISO datetime format uses ":" but not
    "_", let's
    replace ":" with "_"
    :param string: str
    :return: datetime.datetime object
    """
    return parser.parse(string.replace("_plus_", "+").replace("_", ":"))


class BaseGenerator:
    def __init__(self) -> None:
        pass

    @staticmethod
    def serialize_pod(pod: k8s.V1Pod) -> dict:
        """
        Converts a k8s.V1Pod into a jsonified object
        :param pod: k8s.V1Pod object
        :return: Serialized version of the pod returned as dict
        """
        api_client = ApiClient()
        return api_client.sanitize_for_serialization(pod)

    @staticmethod
    def deserialize_model_file(
        path: str, resource_type: str
    ) -> Union[k8s.V1Pod, k8s.V1Job]:
        """
        :param path: Path to the file
        :param resource_type: pod or job
        :return: a kubernetes.client.models.V1Pod or V1Job
        Unfortunately we need access to the private method
        ``_ApiClient__deserialize_model`` from the kubernetes client.
        This issue is tracked here; https://github.com/kubernetes-client/python/issues/977.
        """
        if os.path.exists(path):
            with open(path) as stream:
                workload = safe_load_yaml_io(stream)
        else:
            workload = safe_load_yaml_io(path)

        # pylint: disable=protected-access
        return BaseGenerator.deserialize_model_dict(workload, resource_type)

    @staticmethod
    def deserialize_model_dict(
        workload_dict: dict, resource_type: str
    ) -> Union[k8s.V1Pod, k8s.V1Job, None]:  # type: ignore
        """
        Deserializes python dictionary to k8s.V1Pod
        :param workload_dict: Serialized dict of k8s.V1Pod or K8s.V1Job object
        :param resource_type: pod or job
        :return: De-serialized k8s.V1Pod
        """
        # TODO: Add resource_type validation
        api_client = ApiClient()
        if resource_type == "pod":
            return api_client._ApiClient__deserialize_model(
                workload_dict, k8s.V1Pod
            )  # pylint: disable=W0212
        elif resource_type == "job":
            return api_client._ApiClient__deserialize_model(
                workload_dict, k8s.V1Job
            )  # pylint: disable=W0212
        elif resource_type == "service":
            return api_client._ApiClient__deserialize_model(
                workload_dict, k8s.V1Service
            )  # pylint: disable=W0212
        else:
            return None

    @staticmethod
    def make_unique_k8s_workload_id(
        pod_id: str, unique_pod_name_suffix: str = None
    ) -> Optional[str]:
        r"""
        Kubernetes pod names must consist of one or more lowercase
        rfc1035/rfc1123 labels separated by '.' with a maximum length of 253
        characters. Each label has a maximum length of 63 characters.
        Name must pass the following regex for validation
        ``^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$``
        For more details, see:
        https://github.com/kubernetes/kubernetes/blob/release-1.1/docs/design/identifiers.md
        :param pod_id: a dag_id with only alphanumeric characters
        :param unique_pod_name_suffix: a value to overwrite auto-gen uuid
        :return: ``str`` valid Pod name of appropriate length
        """
        if not pod_id:
            return None

        if not unique_pod_name_suffix:
            safe_uuid = (
                uuid.uuid4().hex
            )  # safe uuid will always be less than 63 chars
        else:
            safe_uuid = unique_pod_name_suffix
        # Strip trailing '-' and '.' as they can't be followed by '.'
        trimmed_pod_id = pod_id[:MAX_LABEL_LEN].rstrip("-.")
        safe_pod_id = f"{trimmed_pod_id}-{safe_uuid}"
        return safe_pod_id
