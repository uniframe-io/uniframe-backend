from datetime import timedelta
from typing import Dict

from pydantic import BaseModel

from server.utils.parser import load_yaml


class NmTaskResourceLimit(BaseModel):
    nr_cpu: float
    mem_size: int


class UserUIPermission(BaseModel):
    change_task_ttl: bool
    compute_resource_permission: Dict[str, bool]
    max_upload_dataset_size: int  # unit: Mib. 1 Mb = 1 * 1024 * 1024


class LimitCompute(BaseModel):
    """
    LImitation for task
    - max_rt_nr_queries: max query string in real-time task
    - max_running_task_nr: max running task in parallel
    """

    max_rt_nr_queries: int
    max_running_task_nr: int
    max_running_api_call_per_month: int


class LimitNmCfg(BaseModel):
    """
    :field nm_task_name_min_len: name matching task name minmal string length
    :field nm_task_name_max_len: name matching task name max string length
    :field nm_task_desc_max_len: name matching task description max string length

    :field max_matching_nr: name matching max number of matching result
    :field running_task_min_ttl: number of second a name matching task TTL
    """

    nm_task_name_min_len: int
    nm_task_name_max_len: int
    nm_task_desc_max_len: int

    max_matching_nr: int
    running_task_min_ttl: timedelta


class GlobalLimitationConfig(BaseModel):
    """Name matching limitation configuration"""

    nm_cfg: LimitNmCfg
    task_pod_cfg: Dict[str, NmTaskResourceLimit]

    @classmethod
    def load(
        cls,
        config_f: str = "conf/limitation-global.yaml",
    ) -> "GlobalLimitationConfig":
        cfg_dict = load_yaml(config_f)
        limit_config = GlobalLimitationConfig(**cfg_dict)
        return limit_config


class UserLimitationConfig(BaseModel):
    """user limitation configuration"""

    compute: LimitCompute
    ui_permission: UserUIPermission

    @classmethod
    def load(
        cls,
        premium_user_type: str,
    ) -> "UserLimitationConfig":
        cfg_dict = load_yaml(f"conf/limitation-{premium_user_type}.yaml")
        limit_config = UserLimitationConfig(**cfg_dict)
        return limit_config
