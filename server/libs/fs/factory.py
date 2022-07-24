import hashlib
import os
import traceback
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import awswrangler as wr
import requests
from pandas.core.frame import DataFrame

from server.core.exception import EXCEPTION_LIB
from server.libs.fs.s3 import S3Helper
from server.settings import API_SETTING
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import api_logger as logger


class NmFileStoreAbcFactory(ABC):
    @abstractmethod
    def get_upload_object_presigned_url(self, **kwargs: Any) -> str:
        pass

    @abstractmethod
    def get_download_object_presigned_url(self, **kwargs: Any) -> str:
        pass

    @abstractmethod
    def generate_fs_prefix(self, **kwargs: Any) -> Any:
        pass

    @abstractmethod
    def upload_to_file_store(self, **kwargs: Any) -> Any:
        pass

    @abstractmethod
    def get_etag_from_file_store(self, **kwargs: Any) -> str:
        pass

    @abstractmethod
    def get_object_url(self, **kwargs: Any) -> str:
        pass

    @abstractmethod
    def save_df(self, result: DataFrame, location: str) -> Any:
        pass

    @abstractmethod
    def delete_object(self, **kwargs: Any) -> None:
        pass

    @classmethod
    def make_concrete(cls) -> "NmFileStoreAbcFactory":
        """The factory method to load name matching metadata factory"""

        NM_FILE_STORE_FACTORY_DICT = {
            "s3": S3NmFileStoreFactory,
            "localfs": LocalNmFileStoreFactory,
        }
        return NM_FILE_STORE_FACTORY_DICT[GLOBAL_CONFIG.file_store]()


class S3NmFileStoreFactory(NmFileStoreAbcFactory):
    def __init__(self) -> None:
        self.s3_helper = S3Helper()

    def get_upload_object_presigned_url(
        self,
        **kwargs: Any,
    ) -> str:
        """
        get presigned url
        :param bucket_name:
        :param key_name:
        :param expiry_in_sec:
        :return:
        """
        resp = self.s3_helper.get_object_presigned_url(
            kwargs["bucket_name"],
            kwargs["key_name"],
            kwargs["expiry_in_sec"],
            client_method="put_object",
        )
        return str(resp.get("data"))

    def get_download_object_presigned_url(
        self,
        **kwargs: Any,
    ) -> str:
        """
        get presigned url
        :param bucket_name:
        :param key_name:
        :param expiry_in_sec:
        :return:
        """
        resp = self.s3_helper.get_object_presigned_url(
            kwargs["bucket_name"],
            kwargs["key_name"],
            kwargs["expiry_in_sec"],
            client_method="get_object",
        )
        return str(resp.get("data"))

    def generate_fs_prefix(self, **kwargs: Any) -> Any:
        """
        get s3 object location
        """
        return "s3:/"

    def upload_to_file_store(self, **kwargs: Any) -> Any:
        """
        use pre-signed URL to put object on S3
        :param kwargs:
        :return:
        """
        resp = requests.put(kwargs["url"], data=kwargs["data"])
        if resp.status_code != 200:
            logger.error(
                f"[upload_file] PLATFORM__AWS__S3__UPLOAD_FILE_ERROR: error [{resp.json()}]"
            )
            raise EXCEPTION_LIB.PLATFORM__AWS__S3__UPLOAD_FILE_ERROR.value(
                f"upload file error: presigned url {kwargs['url']}"
            )
        return resp

    def get_etag_from_file_store(self, **kwargs: Any) -> str:
        """
        get object ETag from S3
        :param kwargs:
        :return:
        """
        return self.s3_helper.get_object_etag(
            kwargs["bucket_name"], kwargs["key_name"]
        )

    def get_object_url(self, **kwargs: Any) -> str:
        """
        get object url
        @param kwargs:
        @return:
        """
        pass

    def save_df(self, result: DataFrame, location: str) -> None:
        wr.s3.to_csv(result, location, index=False)

    def delete_object(self, **kwargs: Any) -> None:
        self.s3_helper.delete_object(kwargs["bucket_name"], kwargs["key_name"])


class LocalNmFileStoreFactory(NmFileStoreAbcFactory):
    def get_upload_object_presigned_url(
        self,
        **kwargs: Any,
    ) -> str:
        """
        get presigned url
        :param bucket_name:
        :param key_name:
        :param expiry_in_sec:
        :return:
        """
        cwd = Path.cwd()
        return f"{cwd}/{API_SETTING.LOCALFS_VOLUME_LOCATION}/{kwargs['bucket_name']}/{kwargs['key_name']}"

    def get_download_object_presigned_url(
        self,
        **kwargs: Any,
    ) -> str:
        """
        get presigned url
        :param bucket_name:
        :param key_name:
        :param expiry_in_sec:
        :return:
        """
        return f"{kwargs['bucket_name']}/{kwargs['key_name']}"

    def generate_fs_prefix(self, **kwargs: Any) -> Any:
        """
        get s3 object location
        """
        cwd = Path.cwd()
        return f"{cwd}/{API_SETTING.LOCALFS_VOLUME_LOCATION}"

    def upload_to_file_store(self, **kwargs: Any) -> Any:
        """
        use pre-signed URL to put object on localfs
        :param kwargs:
        :return:
        """
        p = Path(kwargs["url"])

        # p is the file location
        # we need to test if the parent folder exists or not
        if not p.parent.exists():
            os.makedirs(p.parent)
        try:
            with p.open("wb") as f:
                f.write(kwargs["data"])
        except Exception as e:
            traceback.print_exc()
            err_msg = str(e)
            logger.error(
                f"[upload_file] PLATFORM__LOCALFS__WRITE_ERROR: error [{err_msg}]"
            )
            raise EXCEPTION_LIB.PLATFORM__LOCALFS__WRITE_ERROR.value(
                f"upload file error: presigned url {kwargs['url']}"
            )

    def get_etag_from_file_store(self, **kwargs: Any) -> str:
        """
        get object ETag from localfs
        :param kwargs:
        :return:
        """
        cwd = Path.cwd()
        p = Path(
            f"{cwd}/{API_SETTING.LOCALFS_VOLUME_LOCATION}/{kwargs['bucket_name']}/{kwargs['key_name']}"
        )
        try:
            with p.open("rb") as f:
                content = f.read()
                m = hashlib.md5(content)
                return m.hexdigest()
        except Exception as e:
            traceback.print_exc()
            err_msg = str(e)
            logger.error(
                f"[upload_file] PLATFORM__LOCALFS__WRITE_ERROR: error [{err_msg}]"
            )
            raise EXCEPTION_LIB.PLATFORM__LOCALFS__WRITE_ERROR.value(
                f"upload file error: presigned url {p}"
            )

    def get_object_url(self, **kwargs: Any) -> str:
        """
        get object url
        @param kwargs:
        @return:
        """
        pass

    def save_df(self, result: DataFrame, location: str) -> Any:
        # check parent folder and created if not exists
        p = Path(location)
        if not p.parent.exists():
            os.makedirs(p.parent)

        result.to_csv(location, index=False)

    def delete_object(self, **kwargs: Any) -> None:
        cwd = Path.cwd()
        file_path = f"{cwd}/{API_SETTING.LOCALFS_VOLUME_LOCATION}/{kwargs['bucket_name']}/{kwargs['key_name']}"
        path = Path(file_path)
        if path.exists():
            os.remove(file_path)


FILE_STORE_FACTORY = NmFileStoreAbcFactory.make_concrete()
