import os
from abc import ABC, abstractmethod

import boto3

from server.settings.global_sys_config import GLOBAL_CONFIG


class ContainerRegistryFactory(ABC):
    @abstractmethod
    def get_backend_container_image_url(self, tag: str) -> str:
        pass

    @classmethod
    def make_concrete(cls) -> "ContainerRegistryFactory":
        """The factory method to docker factory"""

        # TODO: add other method when deploy to Azure or other environment
        return AWSECRFactory()


class AWSECRFactory(ContainerRegistryFactory):
    def __init__(self) -> None:
        client = boto3.client("sts")
        self.account_id = client.get_caller_identity()["Account"]
        self.aws_region = GLOBAL_CONFIG.region.value
        self.product_prefix = os.getenv("PRODUCT_PREFIX")
        self.deploy_env = os.getenv("DEPLOY_ENV")

    def get_backend_container_image_url(self, tag: str) -> str:
        """
        get backend docker url
        """
        return f"{self.account_id}.dkr.ecr.{self.aws_region}.amazonaws.com/{self.product_prefix}-{self.deploy_env}-backend:{tag}"
