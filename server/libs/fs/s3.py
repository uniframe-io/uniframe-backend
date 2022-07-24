import traceback

import boto3  # type: ignore
from botocore.exceptions import ClientError

from server.core.exception import EXCEPTION_LIB
from server.settings.global_sys_config import GLOBAL_CONFIG


class S3Helper(object):
    """
    S3 helper class that manipulates files against S3
    """

    def __init__(self, region_name: str = GLOBAL_CONFIG.region):
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.s3_resource = boto3.resource("s3", region_name=region_name)

    def get_object_presigned_url(
        self,
        bucket_name: str,
        key_name: str,
        expiry_in_sec: int,
        client_method: str = "put_object",
    ) -> dict:
        if client_method not in ["put_object", "get_object"]:
            raise EXCEPTION_LIB.PLATFORM__AWS__S3__GENERATE_PRESIGN_URL_ERROR.value(
                "ClientMethod should be in [put_object, get_object]"
            )

        try:
            url = self.s3_client.generate_presigned_url(
                client_method,
                Params={"Bucket": bucket_name, "Key": key_name},
                ExpiresIn=expiry_in_sec,
            )
            return {"status_code": 200, "data": url}
        except ClientError:
            traceback.print_exc()
            raise EXCEPTION_LIB.PLATFORM__AWS__S3__CLIENT_ERROR.value(
                "AWS S3 generate_presigned_url function failed"
            )

    def get_object_etag(self, bucket_name: str, key_name: str) -> str:
        try:
            s3_object = self.s3_client.get_object(
                Bucket=bucket_name, Key=key_name
            )
            return s3_object.get("ETag").strip('"')
        except ClientError:
            traceback.print_exc()
            raise EXCEPTION_LIB.PLATFORM__AWS__S3__CLIENT_ERROR.value(
                "AWS S3 get object function failed by bucket and key"
            )

    def get_object_url(
        self, bucket_name: str, key_name: str, expiry_in_sec: int
    ) -> str:
        pass

    def delete_object(self, bucket_name: str, key_name: str) -> None:
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=key_name)
        except ClientError:
            traceback.print_exc()
            raise EXCEPTION_LIB.PLATFORM__AWS__S3__CLIENT_ERROR.value(
                "AWS S3 delete object function failed by bucket and key"
            )
