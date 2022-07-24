import logging.config
from typing import Any

from server.utils.parser import load_yaml


def init_logging() -> Any:
    """
    loading the config file to init the logger
    :return:
    """
    logging_config = load_yaml("conf/logger_cfg.yaml")
    logging.config.dictConfig(logging_config)

    return logging


api_logger = init_logging().getLogger("fastapi")
compute_logger = init_logging().getLogger("compute")
nm_algo_logger = init_logging().getLogger("nm_algo")
app_config_logger = init_logging().getLogger("app_config")
app_dataset_logger = init_logging().getLogger("app_dataset")
app_group_logger = init_logging().getLogger("app_group")
app_media_logger = init_logging().getLogger("app_media")
app_nm_task_logger = init_logging().getLogger("app_nm_task")
app_oauth_logger = init_logging().getLogger("app_oauth")
app_permission_logger = init_logging().getLogger("app_permission")
app_stat_logger = init_logging().getLogger("app_stat")
app_user_logger = init_logging().getLogger("app_user")
k8s_client_logger = init_logging().getLogger("k8s_command")
test_logger = init_logging().getLogger("test")
