from typing import Dict

from fastapi.testclient import TestClient

from server.apps.nm_task.schemas import NmTaskCreateDTO
from server.settings import API_SETTING
from server.utils.parser import load_yaml


def test_get_nm_batch_task_defaults(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
) -> None:
    cfg_dict = load_yaml("./conf/nm-task-batch-default.yaml")
    nm_cfg_defaults = NmTaskCreateDTO(**cfg_dict)

    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/config/defaults/nm/batch",
        headers=dummy_user_token_header,
    )
    resp = response.json()
    assert response.status_code == 200
    assert NmTaskCreateDTO(**resp) == nm_cfg_defaults


def test_get_nm_rt_task_defaults(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
) -> None:
    cfg_dict = load_yaml("./conf/nm-task-rt-default.yaml")
    nm_cfg_defaults = NmTaskCreateDTO(**cfg_dict)

    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/config/defaults/nm/real-time",
        headers=dummy_user_token_header,
    )
    resp = response.json()
    assert response.status_code == 200
    assert NmTaskCreateDTO(**resp) == nm_cfg_defaults
