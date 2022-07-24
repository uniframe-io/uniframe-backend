from typing import Dict, List

import pytest
from fastapi.testclient import TestClient

from api_tests import pytest_utils
from server.apps.group import schemas as group_schemas
from server.apps.group.crud import GROUP_CRUD
from server.apps.user import schemas as user_schemas
from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING


def test_create_group(
    api_client: TestClient,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user: user_schemas.UserDO,
    do_dummy_group: group_schemas.GroupDO,
) -> None:
    # create anther group with the same name, an exception should be raised
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/groups",
        headers=dummy_user_token_header,
        json=group_schemas.GroupCreateDTO(
            name=do_dummy_group.name,
            description="description blablabla",
        ).dict(),  # Important!!! json expect a dictionary
    )

    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.GROUP__CURRENT_GROUP_NAME_ALREADY_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    # sanity check of creating a group
    group_create_dto = group_schemas.GroupCreateDTO(
        name="endpoint_test_group",
        description="description blablabla",
    )
    response = api_client.post(
        f"{API_SETTING.API_V1_STR}/groups",
        headers=dummy_user_token_header,
        json=group_create_dto.dict(),  # Important!!! json expect a dictionary
    )

    assert response.status_code == 200
    dto_group = group_schemas.GroupDTO(**response.json())
    assert dto_group.name == group_create_dto.name
    assert dto_group.description == group_create_dto.description

    # release the resource
    response = api_client.delete(
        f"{API_SETTING.API_V1_STR}/groups/{dto_group.id}",
        headers=dummy_user_token_header,
    )

    return


@pytest.mark.parametrize(
    "do_dummy_user_list,do_dummy_group_list",
    [(1, 2)],
    indirect=["do_dummy_user_list", "do_dummy_group_list"],
)
def test_get_all_groups(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
    do_dummy_group: group_schemas.GroupDO,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user_list: List[user_schemas.UserDO],
    do_dummy_group_list: List[group_schemas.GroupDO],
) -> None:
    # get all groups from dummy user, should has only one group
    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/groups",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 200
    assert len(response.json()) == 3

    # Create a new group by another user, share the new group with dummy user
    do_new_group = GROUP_CRUD.create_group(
        group_schemas.GroupCreateDO(
            name="group_test_2", description="blablabla"
        ),
        do_dummy_user_list[0].id,
    )

    GROUP_CRUD.add_group_member(do_new_group.id, do_dummy_user.id)

    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/groups",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 200
    assert len(response.json()) == 4

    # release resources
    GROUP_CRUD.delete_group_member(do_new_group.id, do_dummy_user.id)
    GROUP_CRUD.delete_group(do_new_group.id)

    return


@pytest.mark.parametrize(
    "do_dummy_user_list", [1], indirect=["do_dummy_user_list"]
)
def test_get_group(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
    do_dummy_group: group_schemas.GroupDO,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    # get a random group id, an exception should be raised
    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/groups/888888",
        headers=dummy_user_token_header,
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    # TODO: unit test is_active later

    # getting dummy group by dummy user. User is the group owner
    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/groups/{do_dummy_group.id}",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 200
    dto_group = group_schemas.GroupDTO(**response.json())
    assert dto_group.name == do_dummy_group.name
    assert dto_group.description == do_dummy_group.description
    assert dto_group.owner_id == do_dummy_user.id

    # Create a new group by another user, share the new group with dummy user
    do_new_group = GROUP_CRUD.create_group(
        group_schemas.GroupCreateDO(
            name="group_test_2", description="blablabla"
        ),
        do_dummy_user_list[0].id,
    )

    GROUP_CRUD.add_group_member(do_new_group.id, do_dummy_user.id)

    response = api_client.get(
        f"{API_SETTING.API_V1_STR}/groups/{do_new_group.id}",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 200
    dto_group = group_schemas.GroupDTO(**response.json())
    assert dto_group.name == do_new_group.name
    assert dto_group.description == do_new_group.description
    assert dto_group.owner_id == do_dummy_user_list[0].id

    # release resources
    GROUP_CRUD.delete_group_member(do_new_group.id, do_dummy_user.id)
    GROUP_CRUD.delete_group(do_new_group.id)
    return


@pytest.mark.parametrize(
    "do_dummy_user_list", [1], indirect=["do_dummy_user_list"]
)
def test_update_group(
    api_client: TestClient,
    do_dummy_group: group_schemas.GroupDO,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    # Update a random group id, an exception should be raised
    response = api_client.put(
        f"{API_SETTING.API_V1_STR}/groups/888888",
        headers=dummy_user_token_header,
        json=group_schemas.GroupUpdateDTO(
            name="random_group_name",
            description="description blablabla",
        ).dict(),
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    # TODO: is_active

    # Create a new group by another user, update the group by dummy user
    # an exception should be raise because no permission
    do_new_group = GROUP_CRUD.create_group(
        group_schemas.GroupCreateDO(
            name="group_test_2", description="blablabla"
        ),
        do_dummy_user_list[0].id,
    )

    response = api_client.put(
        f"{API_SETTING.API_V1_STR}/groups/{do_new_group.id}",
        headers=dummy_user_token_header,
        json=group_schemas.GroupUpdateDTO(
            name="random_group_name",
            description="description blablabla",
        ).dict(),
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
            "must have this placeholder string!"
        ),
    )

    GROUP_CRUD.delete_group(do_new_group.id)

    # Update the description
    updated_name = "group_name_updated"
    updated_desc = "description updated"
    response = api_client.put(
        f"{API_SETTING.API_V1_STR}/groups/{do_dummy_group.id}",
        headers=dummy_user_token_header,
        json=group_schemas.GroupUpdateDTO(
            name=updated_name,
            description=updated_desc,
        ).dict(),
    )
    assert response.status_code == 200
    dto_group = group_schemas.GroupDTO(**response.json())
    assert dto_group.name == updated_name
    assert dto_group.description == updated_desc

    return


@pytest.mark.parametrize(
    "do_dummy_user_list", [1], indirect=["do_dummy_user_list"]
)
def test_delete_group(
    api_client: TestClient,
    do_dummy_user: user_schemas.UserDO,
    dummy_user_token_header: Dict[str, str],
    do_dummy_user_list: List[user_schemas.UserDO],
) -> None:
    # Delete a random group id, an exception should be raised
    response = api_client.delete(
        f"{API_SETTING.API_V1_STR}/groups/888888",
        headers=dummy_user_token_header,
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.GROUP__CURRENT_GROUP_NOT_EXIST.value(
            "must have this placeholder string!"
        ),
    )

    # TODO: is_active

    # Create a new group by another user, delete the group by dummy user
    # an exception should be raise because no permission
    do_new_group = GROUP_CRUD.create_group(
        group_schemas.GroupCreateDO(
            name="group_test_2", description="blablabla"
        ),
        do_dummy_user_list[0].id,
    )

    response = api_client.delete(
        f"{API_SETTING.API_V1_STR}/groups/{do_new_group.id}",
        headers=dummy_user_token_header,
    )
    pytest_utils.assert_endpoint_response(
        response,
        EXCEPTION_LIB.GROUP__CURRENT_USER_HAS_NO_PERMISSION.value(
            "must have this placeholder string!"
        ),
    )

    GROUP_CRUD.delete_group(do_new_group.id)

    # Create a new group by dummy user, and delete by dummy user
    do_new_group = GROUP_CRUD.create_group(
        group_schemas.GroupCreateDO(
            name="group_test_2", description="blablabla"
        ),
        do_dummy_user.id,
    )

    response = api_client.delete(
        f"{API_SETTING.API_V1_STR}/groups/{do_new_group.id}",
        headers=dummy_user_token_header,
    )
    assert response.status_code == 200
    assert response.json() == "Delete succeed"

    return


def test_get_group_members() -> None:
    # TODO: add the tests
    return


def test_set_group_members() -> None:
    # TODO: add the tests
    return
