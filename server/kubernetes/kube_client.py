from typing import Optional, Union

from server.settings.global_sys_config import GlobalSysConfig
from server.settings.logger import k8s_client_logger as logger

GLOBAL_CONFIG = GlobalSysConfig.load()


try:
    from kubernetes import client, config
    from kubernetes.client import Configuration
    from kubernetes.client.api_client import ApiClient
    from kubernetes.client.rest import (
        ApiException,  # pylint: disable=unused-import
    )

    from server.kubernetes.refresh_config import (  # pylint: disable=ungrouped-imports
        RefreshConfiguration,
        load_kube_config,
    )

    has_kubernetes = True

    def _get_kube_config(
        in_cluster: bool,
        cluster_context: Optional[str],
        config_file: Optional[str],
    ) -> Optional[Configuration]:
        if in_cluster:
            # load_incluster_config set default configuration with config populated by k8s
            config.load_incluster_config()
            return None
        else:
            # this block can be replaced with just config.load_kube_config once
            # refresh_config module is replaced with upstream fix
            cfg = RefreshConfiguration()
            load_kube_config(
                client_configuration=cfg,
                config_file=config_file,
                context=cluster_context,
            )
            return cfg

    def _get_client_with_patched_configuration(
        cfg: Optional[Configuration],
        client_api_version: Optional[str] = "str",
    ) -> Union[client.CoreV1Api, client.BatchV1Api, None]:
        """
        This is a workaround for supporting api token refresh in k8s client.
        The function can be replace with `return client.CoreV1Api()` once the
        upstream client supports token refresh.
        """
        if client_api_version not in ["CoreV1Api", "BatchV1Api"]:
            raise _import_err

        if cfg:
            if client_api_version == "CoreV1Api":
                return client.CoreV1Api(api_client=ApiClient(configuration=cfg))
            elif client_api_version == "BatchV1Api":
                return client.BatchV1Api(
                    api_client=ApiClient(configuration=cfg)
                )
            else:
                return None
        else:
            if client_api_version == "CoreV1Api":
                return client.CoreV1Api()
            elif client_api_version == "BatchV1Api":
                return client.BatchV1Api()
            else:
                return None

    def _disable_verify_ssl() -> None:
        client_config = Configuration()
        client_config.verify_ssl = False
        Configuration.set_default(client_config)


except ImportError as e:
    # We need an exception class to be able to use it in ``except`` elsewhere
    # in the code base
    ApiException = BaseException
    has_kubernetes = False
    _import_err = e


def _enable_tcp_keepalive() -> None:
    """
    This function enables TCP keepalive mechanism. This prevents urllib3 connection
    to hang indefinitely when idle connection is time-outed on services like cloud
    load balancers or firewalls.
    See https://github.com/apache/airflow/pull/11406 for detailed explanation.
    Please ping @michalmisiewicz or @dimberman in the PR if you want to modify this function.
    """
    import socket

    from urllib3.connection import HTTPConnection, HTTPSConnection

    # tcp_keep_idle = conf.getint('kubernetes', 'tcp_keep_idle')
    tcp_keep_idle = GLOBAL_CONFIG.kubernetes.tcp_keep_idle
    # tcp_keep_intvl = conf.getint('kubernetes', 'tcp_keep_intvl')
    tcp_keep_intvl = GLOBAL_CONFIG.kubernetes.tcp_keep_intvl
    # tcp_keep_cnt = conf.getint('kubernetes', 'tcp_keep_cnt')
    tcp_keep_cnt = GLOBAL_CONFIG.kubernetes.tcp_keep_cnt

    socket_options = [(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)]

    if hasattr(socket, "TCP_KEEPIDLE"):
        socket_options.append(
            (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, tcp_keep_idle)
        )
    else:
        logger.warning("Unable to set TCP_KEEPIDLE on this platform")

    if hasattr(socket, "TCP_KEEPINTVL"):
        socket_options.append(
            (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, tcp_keep_intvl)
        )
    else:
        logger.warning("Unable to set TCP_KEEPINTVL on this platform")

    if hasattr(socket, "TCP_KEEPCNT"):
        socket_options.append(
            (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, tcp_keep_cnt)
        )
    else:
        logger.warning("Unable to set TCP_KEEPCNT on this platform")

    HTTPSConnection.default_socket_options = (
        HTTPSConnection.default_socket_options + socket_options
    )
    HTTPConnection.default_socket_options = (
        HTTPConnection.default_socket_options + socket_options
    )


def get_kube_client(
    # in_cluster: bool = conf.getboolean('kubernetes', 'in_cluster'),
    in_cluster: bool = GLOBAL_CONFIG.kubernetes.in_cluster,
    cluster_context: Optional[str] = None,
    config_file: Optional[str] = None,
    client_api_version: Optional[str] = "CoreV1Api",
) -> Union[client.CoreV1Api, client.BatchV1Api]:
    """
    Retrieves Kubernetes client
    :param in_cluster: whether we are in cluster
    :type in_cluster: bool
    :param cluster_context: context of the cluster
    :type cluster_context: str
    :param config_file: configuration file
    :type config_file: str
    :return kubernetes client
    :rtype client.CoreV1Api
    :param client_api_version: CoreV1Api for pod, BatchV1Api for job, default value is CoreV1Api
    :rtype client.CoreV1Api or client.BatchV1Api
    """
    if not has_kubernetes:
        raise _import_err

    if not in_cluster:
        if cluster_context is None:
            cluster_context = GLOBAL_CONFIG.kubernetes.cluster_context
        if config_file is None:
            # config_file = conf.get('kubernetes', 'config_file', fallback=None)
            config_file = GLOBAL_CONFIG.kubernetes.config_file

    # if conf.getboolean('kubernetes', 'enable_tcp_keepalive'):
    if GLOBAL_CONFIG.kubernetes.enable_tcp_keepalive:
        _enable_tcp_keepalive()

    # if not conf.getboolean('kubernetes', 'verify_ssl'):
    if not GLOBAL_CONFIG.kubernetes.verify_ssl:
        _disable_verify_ssl()

    client_conf = _get_kube_config(in_cluster, cluster_context, config_file)
    return _get_client_with_patched_configuration(
        client_conf, client_api_version
    )
