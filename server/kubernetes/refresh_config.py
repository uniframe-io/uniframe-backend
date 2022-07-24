import calendar
import logging
import os
import time
from typing import Optional, Union

from dateutil.parser import parse
from kubernetes.client import Configuration
from kubernetes.config.exec_provider import ExecProvider
from kubernetes.config.kube_config import (
    KUBE_CONFIG_DEFAULT_LOCATION,
    KubeConfigLoader,
)

from server.utils.parser import safe_load_yaml_io


def _parse_timestamp(ts_str: str) -> int:
    parsed_dt = parse(ts_str)
    return calendar.timegm(parsed_dt.timetuple())


class RefreshKubeConfigLoader(KubeConfigLoader):
    """
    Patched KubeConfigLoader, this subclass takes expirationTimestamp into
    account and sets api key refresh callback hook in Configuration object
    """

    def __init__(self, *args, **kwargs):  # type: ignore
        KubeConfigLoader.__init__(self, *args, **kwargs)
        self.api_key_expire_ts = None

    def _load_from_exec_plugin(self) -> Union[bool, None]:
        """
        We override _load_from_exec_plugin method to also read and store
        expiration timestamp for aws-iam-authenticator. It will be later
        used for api token refresh.
        """
        if "exec" not in self._user:
            return None
        try:
            status = ExecProvider(self._user["exec"]).run()
            if "token" not in status:
                logging.error("exec: missing token field in plugin output")
                return None
            self.token = f"Bearer {status['token']}"  # pylint: disable=W0201
            ts_str = status.get("expirationTimestamp")
            if ts_str:
                self.api_key_expire_ts = _parse_timestamp(ts_str)
            return True
        except Exception as e:  # pylint: disable=W0703
            logging.error(str(e))
            return None

    def refresh_api_key(self, client_configuration) -> None:  # type: ignore
        """Refresh API key if expired"""
        if self.api_key_expire_ts and time.time() >= self.api_key_expire_ts:
            self.load_and_set(client_configuration)

    def load_and_set(self, client_configuration) -> None:  # type: ignore
        KubeConfigLoader.load_and_set(self, client_configuration)
        client_configuration.refresh_api_key = self.refresh_api_key


class RefreshConfiguration(Configuration):
    """
    Patched Configuration, this subclass takes api key refresh callback hook
    into account
    """

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        Configuration.__init__(self, *args, **kwargs)
        self.refresh_api_key = None

    def get_api_key_with_prefix(self, identifier: str) -> str:
        if self.refresh_api_key:
            self.refresh_api_key(self)  # pylint: disable=E1102
        return Configuration.get_api_key_with_prefix(self, identifier)


def _get_kube_config_loader_for_yaml_file(
    filename: str, **kwargs: Union[dict, None]
) -> Optional[RefreshKubeConfigLoader]:
    """
    Adapted from the upstream _get_kube_config_loader_for_yaml_file function, changed
    KubeConfigLoader to RefreshKubeConfigLoader
    """
    with open(filename) as f:
        return RefreshKubeConfigLoader(
            config_dict=safe_load_yaml_io(f),
            config_base_path=os.path.abspath(os.path.dirname(filename)),
            **kwargs,
        )


def load_kube_config(client_configuration: "RefreshKubeConfigLoader", config_file: str = None, context=None) -> None:  # type: ignore
    """
    Adapted from the upstream load_kube_config function, changes:
        - removed persist_config argument since it's not being used
        - remove `client_configuration is None` branch since we always pass
        in client configuration
    """
    if config_file is None:
        config_file = os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION)

    loader = _get_kube_config_loader_for_yaml_file(
        config_file, active_context=context, config_persister=None
    )
    loader.load_and_set(client_configuration)  # type: ignore
