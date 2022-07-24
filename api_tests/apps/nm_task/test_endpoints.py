from typing import Dict

from fastapi.testclient import TestClient

from server.apps.nm_task import schemas
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.settings import API_SETTING


def test_create_nm_task(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:
    # test real-time nm task
    nm_task_create = schemas.NmTaskCreateDTO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )

    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/tasks/nm",
        headers=dummy_user_token_header,
        json=nm_task_create.dict(),  # Important!!! json expect a dictionary
    )

    resp = response.json()
    assert response.status_code == 200
    assert resp["type"] == "NAME_MATCHING_REALTIME"

    NM_TASK_CRUD.delete_task(resp["id"])

    # test batch-time nm task
    nm_task_create = schemas.NmTaskCreateDTO(
        type=schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH,
        name="dummy",
        description="dummy description",
        is_public=False,
        ext_info=schemas.NmCfgBatchSchema(**do_nm_batch_task_cfg_dict),
    )

    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/tasks/nm",
        headers=dummy_user_token_header,
        json=nm_task_create.dict(),  # Important!!! json expect a dictionary
    )
    assert response.status_code == 200
    resp = response.json()
    assert resp["type"] == "NAME_MATCHING_BATCH"

    NM_TASK_CRUD.delete_task(resp["id"])


def test_create_nm_task_invalid_input(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_nm_batch_task_cfg_dict: dict,
    do_nm_rt_task_cfg_dict: dict,
) -> None:

    # 1. test invalid input: empty payload
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/tasks/nm",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 422

    # # 2. test invalid input: some incorrect parameters
    # nm_task_create = schemas.NmTaskCreateDTO(
    #     type=schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
    #     name="dummy",
    #     description="dummy description",
    #     is_public=False,
    # )
    # response = api_client.post(
    #     f"{API_SETTING.API_V1_STR}/api/v1/tasks/nm",
    #     headers=dummy_user_token_header,
    #     json=nm_task_create.dict(),  # Important!!! json expect a dictionary
    # )
    # assert response.status_code == 422
