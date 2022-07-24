from abc import ABC, abstractmethod
from functools import reduce
from typing import List, Optional

from kubernetes.client import models as k8s


class K8SModel(ABC):
    """
    These Airflow Kubernetes models are here for backwards compatibility
    reasons only. Ideally clients should use the kubernetes api
    and the process of
        client input -> Airflow k8s models -> k8s models
    can be avoided. All of these models implement the
    `attach_to_pod` method so that they integrate with the kubernetes client.
    """

    @abstractmethod
    def attach_to_pod(self, pod: k8s.V1Pod) -> k8s.V1Pod:
        """
        :param pod: A pod to attach this Kubernetes object to
        :type pod: kubernetes.client.models.V1Pod
        :return: The pod with the object attached
        """


def append_to_pod(
    pod: k8s.V1Pod, k8s_objects: Optional[List[K8SModel]]
) -> object:
    """
    :param pod: A pod to attach a list of Kubernetes objects to
    :type pod: kubernetes.client.models.V1Pod
    :param k8s_objects: a potential None list of K8SModels
    :type k8s_objects: Optional[List[K8SModel]]
    :return: pod with the objects attached if they exist
    """
    if not k8s_objects:
        return pod
    return reduce(lambda p, o: o.attach_to_pod(p), k8s_objects, pod)
