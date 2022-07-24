import enum
import os

from pydantic import BaseModel
from pydantic.dataclasses import dataclass

from server.utils.parser import load_yaml


class PLATFORM_OPTIONS(str, enum.Enum):
    AWS = "aws"


class IO_TYPE_FILESTORE(str, enum.Enum):
    S3 = "s3"
    LOCALFS = "localfs"


class IO_TYPE_APISTORE(str, enum.Enum):
    PG = "pg"


class API_SECRET_ALGORITHM(str, enum.Enum):
    HS256 = "HS256"


class PLATFORM_REGION(str, enum.Enum):
    EU_WEST_1 = "eu-west-1"


class PLATFORM_AWS_REGION(str, enum.Enum):
    EU_WEST_1 = "eu-west-1"


class DYNAMIC_RESOURCE_VALIDITY(int, enum.Enum):
    PUT_OBJECT_URL_TTL = 1800
    GET_OBJECT_URL_TTL = 1800


class EXECUTOR(str, enum.Enum):
    CeleryExecutor = "CeleryExecutor"
    LocalExecutor = "LocalExecutor"
    KubernetesExecutor = "KubernetesExecutor"


class KUBERNETES(BaseModel):
    """K8S"""

    in_cluster: bool
    tcp_keep_idle: int
    tcp_keep_intvl: int
    tcp_keep_cnt: int
    cluster_context: str = None  # type: ignore
    config_file: str = None  # type: ignore
    enable_tcp_keepalive: bool
    verify_ssl: bool


@dataclass
class GlobalSysConfig:
    """Global System configuration
    :field platform: deployment platform, AWS/Azure/local...
    :field metadata_store: where to store metadata, dynamodb/localfs/...
    :field file_store: where to store matching file data, s3/localfs
    """

    platform: PLATFORM_OPTIONS
    file_store: IO_TYPE_FILESTORE
    localfs_volume_loc: str
    api_store: IO_TYPE_APISTORE
    region: PLATFORM_AWS_REGION
    bucket_name: str
    filestore_put_object_url_ttl: DYNAMIC_RESOURCE_VALIDITY
    filestore_get_object_url_ttl: DYNAMIC_RESOURCE_VALIDITY
    executor: EXECUTOR
    kubernetes: KUBERNETES
    app_log_group: str

    @classmethod
    def load(
        cls,
    ) -> "GlobalSysConfig":

        config_f = f"conf/global-sys-config_{os.getenv('DEPLOY_ENV')}.yaml"
        cfg_dict = load_yaml(config_f)

        # override bucket name
        global_config = GlobalSysConfig(**cfg_dict)
        global_config.bucket_name = (
            f"{os.getenv('PRODUCT_PREFIX')}-{os.getenv('DEPLOY_ENV')}-data"
        )
        return global_config

    def filestore_is_s3(self) -> bool:
        return self.file_store == IO_TYPE_FILESTORE.S3


GLOBAL_CONFIG: GlobalSysConfig = GlobalSysConfig.load()
