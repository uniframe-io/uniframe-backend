from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from api_tests import pytest_utils
from server.apps.dataset import schemas as dataset_schemas
from server.apps.dataset.crud import DATASET_CRUD
from server.apps.media import schemas as media_schemas
from server.apps.media.crud import MEDIA_CRUD
from server.apps.nm_task import schemas as nm_task_schemas
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.user import schemas as user_schemas
from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING


def test_create_dataset(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_media: media_schemas.MediaDO,
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/datasets",
        headers=dummy_user_token_header,
        json=dataset_schemas.DatasetCreateDTO(
            name="Dummy Dataset",
            description="This is a dummy dataset for unit test",
            media_id=do_dummy_media.id,
        ).dict(),
    )

    assert response.status_code == 200
    dto_dataset = dataset_schemas.DatasetDTO(**response.json())
    assert dto_dataset.name == "Dummy Dataset"
    assert dto_dataset.description == "This is a dummy dataset for unit test"

    DATASET_CRUD.delete_dataset(dto_dataset.id)
    return


def test_create_dataset_name_already_exist(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/datasets",
        headers=dummy_user_token_header,
        json=dataset_schemas.DatasetCreateDTO(
            name="Dummy Dataset",
            description="This is a dummy dataset for unit test",
            media_id=99999,
        ).dict(),
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.DATASET__CURRENT_DATASET_NAME_ALREADY_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    return


def test_create_dataset_media_not_exist(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_media: media_schemas.MediaDO,
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/datasets",
        headers=dummy_user_token_header,
        json=dataset_schemas.DatasetCreateDTO(
            name="Dummy Dataset",
            description="This is a dummy dataset for unit test",
            media_id=do_dummy_media.id + 1,
        ).dict(),
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.MEDIA__CURRENT_MEDIA_NOT_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    return


@pytest.mark.parametrize(
    "do_dummy_user_list", [1], indirect=["do_dummy_user_list"]
)
def test_create_dataset_media_permission_not_allowed(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    do_media_create = media_schemas.MediaCreateDO(
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
        owner_id=do_dummy_user_list[0].id,
    )
    do_media = MEDIA_CRUD.create_media(do_media_create)

    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/datasets",
        headers=dummy_user_token_header,
        json=dataset_schemas.DatasetCreateDTO(
            name="Dummy Dataset",
            description="This is a dummy dataset for unit test",
            media_id=do_media.id,
        ).dict(),
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.MEDIA__CURRENT_USER_HAS_NO_PERMISSION.value(
            "must have this placeholder string!"
        ),
    )

    MEDIA_CRUD.delete_media(do_media.id)
    return


def test_retrieve_dataset(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dummy_dataset.id}",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 200

    dto_dataset = dataset_schemas.DatasetDTO(**response.json())
    assert dto_dataset.name == do_dummy_dataset.name

    return


def test_retrieve_dataset_not_exist(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dummy_dataset.id + 1}",
        headers=dummy_user_token_header,
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    return


def test_retrieve_dataset_permission_not_allowed(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    # TODO current user who is owner or viewer can tetrieve the resource,
    #  will inplement this part when endpoint is ready.

    return


def test_destroy_dataset(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    response = api_client.delete(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dummy_dataset.id}",
        headers=dummy_user_token_header,
    )

    assert response.status_code == 200
    return


def test_destroy_dataset_not_active(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    DATASET_CRUD.update_dataset(
        do_dummy_dataset.id,
        dataset_schemas.DatasetUpdateDO(
            is_active=False,
        ),
    )
    response = api_client.delete(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dummy_dataset.id}",
        headers=dummy_user_token_header,
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.GROUP__CURRENT_DATASET_NOT_ACTIVE.value(
            "must have this placeholder string!"
        ),
    )
    return


def test_destroy_dataset_not_exist(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    response = api_client.delete(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dummy_dataset.id + 1}",
        headers=dummy_user_token_header,
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
            "must have this placeholder string!"
        ),
    )
    return


@pytest.mark.parametrize(
    "do_dummy_user_list", [1], indirect=["do_dummy_user_list"]
)
def test_destroy_dataset_perssion_not_allowed(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    do_media_create = media_schemas.MediaCreateDO(
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
        owner_id=do_dummy_user_list[0].id,
    )
    do_media = MEDIA_CRUD.create_media(do_media_create)

    dataset_create = dataset_schemas.DatasetCreateDO(
        name="Dummy Dataset",
        description="This is a dummy dataset for unit test",
        media_id=do_media.id,
        owner_id=do_dummy_user_list[0].id,
    )

    do_dataset = DATASET_CRUD.create_dataset(dataset_create)

    response = api_client.delete(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dataset.id}",
        headers=dummy_user_token_header,
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "must have this placeholder string!"
        ),
    )

    DATASET_CRUD.delete_dataset(do_dataset.id)
    MEDIA_CRUD.delete_media(do_media.id)

    return


def test_update_dataset(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    response = api_client.patch(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dummy_dataset.id}",
        headers=dummy_user_token_header,
        json=dataset_schemas.DatasetUpdateDTO(
            name="Dummy Dataset Update",
            description="This is a dummy dataset for update unit test",
        ).dict(),
    )
    assert response.status_code == 200

    dto_dataset = dataset_schemas.DatasetDTO(**response.json())
    assert dto_dataset.name == "Dummy Dataset Update"

    return


def test_update_dataset_not_exist(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    response = api_client.patch(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dummy_dataset.id+1}",
        headers=dummy_user_token_header,
        json=dataset_schemas.DatasetUpdateDTO(
            name="Dummy Dataset Update",
            description="This is a dummy dataset for update unit test",
        ).dict(),
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    return


def test_update_dataset_name_already_exist(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:

    response = api_client.patch(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dummy_dataset.id+1}",
        headers=dummy_user_token_header,
        json=dataset_schemas.DatasetUpdateDTO(
            name="Dummy Dataset",
            description="This is a dummy dataset for update unit test",
        ).dict(),
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.DATASET__CURRENT_DATASET_NAME_ALREADY_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    return


@pytest.mark.parametrize(
    "do_dummy_user_list", [1], indirect=["do_dummy_user_list"]
)
def test_update_dataset_permission_not_allowed(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    do_media_create = media_schemas.MediaCreateDO(
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/5da8000df074c754f6bdac341ece2a92.upload_test_file.csv",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
        owner_id=do_dummy_user_list[0].id,
    )
    do_media = MEDIA_CRUD.create_media(do_media_create)

    dataset_create = dataset_schemas.DatasetCreateDO(
        name="Dummy Dataset",
        description="This is a dummy dataset for unit test",
        media_id=do_media.id,
        owner_id=do_dummy_user_list[0].id,
    )

    do_dataset = DATASET_CRUD.create_dataset(dataset_create)

    response = api_client.patch(
        f"{API_SETTING.API_V1_STR}/datasets/{do_dataset.id}",
        headers=dummy_user_token_header,
        json=dataset_schemas.DatasetUpdateDTO(
            name="Dummy Dataset",
            description="This is a dummy dataset for update unit test",
        ).dict(),
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "must have this placeholder string!"
        ),
    )

    DATASET_CRUD.delete_dataset(do_dataset.id)
    MEDIA_CRUD.delete_media(do_media.id)

    return


def test_list_dataset(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_dataset: dataset_schemas.DatasetDO,
) -> None:
    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/datasets",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 200

    assert len(response.json()) == 1

    return


def test_get_dataset_stats(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_nm_rt_task_cfg_dict: dict,
) -> None:
    nm_task_create = nm_task_schemas.NmTaskCreateDTO(
        type=nm_task_schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        name="dummy",
        description="dummy description",
        is_public=False,
        ext_info=nm_task_schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict),
    )

    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/tasks/nm",
        headers=dummy_user_token_header,
        json=nm_task_create.dict(),  # Important!!! json expect a dictionary
    )

    resp = response.json()
    assert response.status_code == 200
    assert resp["type"] == "NAME_MATCHING_REALTIME"

    rt_task_id = resp["id"]

    dataset_id = resp["ext_info"]["gt_dataset_config"]["dataset_id"]

    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/datasets/{dataset_id}/stats",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 200

    dto_dataset_stat = dataset_schemas.DatasetStatDTO(**response.json())
    assert len(dto_dataset_stat.used_by_tasks) == 1

    NM_TASK_CRUD.delete_task(rt_task_id)
