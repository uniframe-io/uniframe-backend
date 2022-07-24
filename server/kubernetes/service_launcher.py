import json
from typing import Optional

from kubernetes import client, watch
from kubernetes.client.models.v1_service import V1Service
from kubernetes.client.rest import ApiException

from server.kubernetes.kube_client import get_kube_client
from server.settings.logger import k8s_client_logger as logger


class ServiceLauncher:
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
            client_api_version="BatchV1Api",
        )
        self._watch = watch.Watch()
        self.logger = logger

    def put_service_async(self, service: V1Service, **kwargs: dict) -> None:
        """Put/Create/Update SERVICE asynchronously"""
        sanitized_service = self._client.api_client.sanitize_for_serialization(
            service
        )
        json_service = json.dumps(sanitized_service, indent=2)

        self.logger.debug("Service Creation Request: \n%s", json_service)
        try:
            resp = self._client.create_namespaced_service(
                body=sanitized_service,
                namespace=service.metadata.namespace,
                **kwargs
            )
            self.logger.debug("Service Creation Response: %s", resp)
        except Exception as e:
            self.logger.exception(
                "Exception when attempting to create Namespaced Service: %s",
                json_service,
            )
            raise e
        return resp

    def delete_service(
        self,
        service: V1Service,
    ) -> None:
        """Delete service"""
        try:
            self._client.delete_namespaced_service(
                service.metadata.name,
                service.metadata.namespace,
                body=client.V1DeleteOptions(propagation_policy="Background"),
            )
        except ApiException as e:
            # If the pod is already deleted
            if e.status != 404:
                raise
