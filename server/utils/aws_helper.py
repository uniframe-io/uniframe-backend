# import datetime
import json
import os

import boto3
from botocore.exceptions import ClientError

from server.core.exception import EXCEPTION_LIB
from server.settings.logger import api_logger as logger

# class SSMParameterStore(object):
#     """
#     Provide a dictionary-like interface to access AWS SSM Parameter Store
#     """

#     def __init__(self, prefix=None, ssm_client=None, ttl=None) -> None:
#         self._prefix = (prefix or "").rstrip("/") + "/"
#         self._client = ssm_client or boto3.client("ssm")
#         self._keys = None
#         self._substores = {}
#         self._ttl = ttl

#     def get(self, name, **kwargs) -> str:
#         assert name, "Name can not be empty"
#         if self._keys is None:
#             self.refresh()

#         abs_key = "%s%s" % (self._prefix, name)
#         if name not in self._keys:
#             if "default" in kwargs:
#                 return kwargs["default"]

#             raise KeyError(name)
#         elif self._keys[name]["type"] == "prefix":
#             if abs_key not in self._substores:
#                 store = self.__class__(
#                     prefix=abs_key, ssm_client=self._client, ttl=self._ttl
#                 )
#                 store._keys = self._keys[name]["children"]
#                 self._substores[abs_key] = store

#             return self._substores[abs_key]
#         else:
#             return self._get_value(name, abs_key)

#     def refresh(self) -> None:
#         self._keys = {}
#         self._substores = {}

#         paginator = self._client.get_paginator("describe_parameters")
#         pager = paginator.paginate(
#             ParameterFilters=[
#                 dict(Key="Path", Option="Recursive", Values=[self._prefix])
#             ]
#         )

#         for page in pager:
#             for p in page["Parameters"]:
#                 paths = p["Name"][len(self._prefix) :].split("/")
#                 self._update_keys(self._keys, paths)

#     @classmethod
#     def _update_keys(cls, keys, paths):
#         name = paths[0]

#         # this is a prefix
#         if len(paths) > 1:
#             if name not in keys:
#                 keys[name] = {"type": "prefix", "children": {}}

#             cls._update_keys(keys[name]["children"], paths[1:])
#         else:
#             keys[name] = {"type": "parameter", "expire": None}

#     def keys(self):
#         if self._keys is None:
#             self.refresh()

#         return self._keys.keys()

#     def _get_value(self, name, abs_key):
#         entry = self._keys[name]

#         # simple ttl
#         if not self._ttl or (
#             entry["expire"] and entry["expire"] <= datetime.datetime.now()
#         ):
#             entry.pop("value", None)

#         if "value" not in entry:
#             parameter = self._client.get_parameter(
#                 Name=abs_key, WithDecryption=True
#             )["Parameter"]
#             value = parameter["Value"]
#             if parameter["Type"] == "StringList":
#                 value = value.split(",")

#             entry["value"] = value

#             if self._ttl:
#                 entry["expire"] = datetime.datetime.now() + datetime.timedelta(
#                     seconds=self._ttl
#                 )
#             else:
#                 entry["expire"] = None

#         return entry["value"]

#     def __contains__(self, name) -> bool:
#         try:
#             self.get(name)
#             return True
#         except Exception:
#             return False

#     def __getitem__(self, name) -> str:
#         return self.get(name)

#     def __setitem__(self, key, value) -> None:
#         raise NotImplementedError()

#     def __delitem__(self, name) -> None:
#         raise NotImplementedError()

#     def __repr__(self) -> str:
#         return "ParameterStore[%s]" % self._prefix


def id_gen(resource_name: str) -> str:
    """
    Get AWS resource id
    """
    if os.getenv("PRODUCT_PREFIX") is None:
        logger.error(
            "[id_gen] GENERAL__ENV_NOT_ASSIGNED: env [PRODUCT_PREFIX] not exist!"
        )
        raise EXCEPTION_LIB.GENERAL__ENV_NOT_ASSIGNED.value(
            "product configuration error. Missing key environment variable. Please contact info@uniframe.io"
        )

    if os.getenv("DEPLOY_ENV") is None:
        logger.error(
            "[id_gen] GENERAL__ENV_NOT_ASSIGNED: env [DEPLOY_ENV] not exist!"
        )
        raise EXCEPTION_LIB.GENERAL__ENV_NOT_ASSIGNED.value(
            "product configuration error. Missing key environment variable. Please contact info@uniframe.io"
        )

    return f"{os.getenv('PRODUCT_PREFIX')}-{os.getenv('DEPLOY_ENV')}-{resource_name}"


def get_secret(secret_name: str, region_name: str) -> str:
    client = boto3.client("secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print("The requested secret " + secret_name + " was not found")
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            print("The request was invalid due to:", e)
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            print("The request had invalid params:", e)
        elif e.response["Error"]["Code"] == "DecryptionFailure":
            print(
                "The requested secret can't be decrypted using the provided KMS key:",
                e,
            )
        elif e.response["Error"]["Code"] == "InternalServiceError":
            print("An error occurred on service side:", e)
        raise EXCEPTION_LIB.AWS__GET_ARC4_SECRET_ERR.value(
            "Could not receive the secret managers value for ARC4 secret"
        )
    else:
        # Secrets Manager decrypts the secret value using the associated KMS CMK
        # Depending on whether the secret was a string or binary, only one of these fields will be populated
        if "SecretString" not in get_secret_value_response:
            raise EXCEPTION_LIB.AWS__GET_ARC4_SECRET_ERR.value(
                "Expect a plaintext secret instead of binary secret"
            )

        text_secret_data = get_secret_value_response["SecretString"]
        secret_value = json.loads(text_secret_data)["password"]

    return secret_value
