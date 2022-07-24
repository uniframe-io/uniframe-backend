import json
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from api_tests import pytest_utils
from server.apps.media import schemas as media_schemas
from server.apps.media.crud import MEDIA_CRUD
from server.apps.user import schemas as user_schemas
from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING


@pytest.fixture()
def dummy_first_n_rows(request: Any) -> List[Dict]:
    nrows = request.param
    top_n_rows = [
        {
            "Company Name": "Amazon",
            "Address": "MountainView, SF, USA",
            "Type": "Tech Giant",
            "Notes": "Amazing",
            "Founded Time": 1997,
        },
        {
            "Company Name": "Google",
            "Address": "San Jose, SF, USA",
            "Type": "Tech Giant",
            "Notes": "Superb",
            "Founded Time": 1998,
        },
        {
            "Company Name": "Sun Analytics",
            "Address": "Utrecht, Netherlands",
            "Type": "Startup",
            "Notes": "Awesome",
            "Founded Time": 2020,
        },
        {
            "Company Name": "Amazon",
            "Address": "MountainView, SF, USA",
            "Type": "Tech Giant",
            "Notes": "Amazing",
            "Founded Time": 1997,
        },
        {
            "Company Name": "Google",
            "Address": "San Jose, SF, USA",
            "Type": "Tech Giant",
            "Notes": "Superb",
            "Founded Time": 1998,
        },
    ]
    return top_n_rows[:nrows]


@pytest.mark.parametrize(
    "dummy_first_n_rows", [5], indirect=["dummy_first_n_rows"]
)
def test_upload_file_csv(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user: user_schemas.UserDO,
    dummy_first_n_rows: List[Dict],
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/medias/upload",
        headers=dummy_user_token_header,
        files={
            "file": (
                "filename",
                open("./api_tests/apps/media/upload_test_file.csv", "rb"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    dto_media = media_schemas.MediaDTO(**response.json())

    assert dto_media.owner_id == do_dummy_user.id

    MEDIA_CRUD.delete_media(dto_media.id)

    first_n_rows = json.loads(dto_media.ext_info.first_n_rows)
    for i in range(5):
        assert first_n_rows[i] == dummy_first_n_rows[i]

    return


@pytest.mark.parametrize(
    "dummy_first_n_rows", [5], indirect=["dummy_first_n_rows"]
)
def test_upload_file_xlsx(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user: user_schemas.UserDO,
    dummy_first_n_rows: List[Dict],
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/medias/upload",
        headers=dummy_user_token_header,
        files={
            "file": (
                "filename",
                open("./api_tests/apps/media/upload_test_file.xlsx", "rb"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    dto_media = media_schemas.MediaDTO(**response.json())

    assert dto_media.owner_id == do_dummy_user.id

    MEDIA_CRUD.delete_media(dto_media.id)

    first_n_rows = json.loads(dto_media.ext_info.first_n_rows)
    for i in range(5):
        assert first_n_rows[i] == dummy_first_n_rows[i]

    return


@pytest.mark.parametrize(
    "dummy_first_n_rows", [5], indirect=["dummy_first_n_rows"]
)
def test_upload_file_xls(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user: user_schemas.UserDO,
    dummy_first_n_rows: List[Dict],
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/medias/upload",
        headers=dummy_user_token_header,
        files={
            "file": (
                "filename",
                open("./api_tests/apps/media/upload_test_file.xls", "rb"),
                "application/vnd.ms-excel",
            )
        },
    )

    assert response.status_code == 200
    dto_media = media_schemas.MediaDTO(**response.json())

    assert dto_media.owner_id == do_dummy_user.id

    MEDIA_CRUD.delete_media(dto_media.id)

    first_n_rows = json.loads(dto_media.ext_info.first_n_rows)
    for i in range(5):
        assert first_n_rows[i] == dummy_first_n_rows[i]
    return


def test_upload_file_error_mime_type(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
) -> None:
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/medias/upload",
        headers=dummy_user_token_header,
        files={
            "file": (
                "filename",
                open("./api_tests/apps/media/upload_test_file.csv", "rb"),
                "image/jpeg",
            )
        },
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.MEDIA__MIME_TYPE_ERROR.value(
            "must have this placeholder string!"
        ),
    )

    return


# TODO: add this test back after adding the checking s3 file
# def test_upload_file_already_exist(
#     api_client: TestClient,
#     dummy_user_token_header: Dict[str, str],
#     do_dummy_media: media_schemas.MediaDO,
# ) -> None:
#     response = api_client.post(
#         f"{API_SETTING.API_V1_STR}/medias/upload",
#         headers=dummy_user_token_header,
#         files={
#             "file": (
#                 "filename",
#                 open("./api_tests/apps/media/upload_test_file.csv", "rb"),
#                 "text/csv",
#             )
#         },
#     )

#     assert response.status_code == 200
#     dto_media = media_schemas.MediaDTO(**response.json())

#     assert dto_media == MEDIA_CRUD.media_do_to_dto(do_dummy_media)

#     return
