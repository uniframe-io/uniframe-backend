# Disable this test so that no email received

# from typing import Dict

# from fastapi.testclient import TestClient

# from server.apps.permission import schemas as perm_schemas
# from server.apps.permission.crud import LOCAL_DEPLOY_USER_CRUD
# from server.apps.user import schemas as user_schemas
# from server.settings import API_SETTING


# def test_request_local_deploy(
#     api_client: TestClient,
#     dummy_user_token_header: Dict[str, str],
#     do_dummy_user: user_schemas.UserDO,
# ) -> None:
#     response = api_client.post(
#         f"{API_SETTING.API_V1_STR}/permission/local-deploy/request",
#         headers=dummy_user_token_header,
#         json=perm_schemas.LocalDeployUserCreateDTO(
#             company="test BV", role="CEO", purpose="test this awesome product"
#         ).dict(),  # Important!!! json expect a dictionary
#     )

#     assert response.status_code == 200
#     assert response.json() == "Local deployment request successfully"

#     return


# def test_approve_local_deploy(
#     api_client: TestClient,
#     super_user_token_header: Dict[str, str],
#     do_dummy_user: user_schemas.UserDO,
#     dummy_user_token_header: Dict[str, str],
# ) -> None:
#     response = api_client.post(
#         f"{API_SETTING.API_V1_STR}/permission/local-deploy/{do_dummy_user.id}/approve",
#         headers=super_user_token_header,
#     )

#     assert response.status_code == 200
#     assert response.json() == "Approve local deploy request successfully"

#     response = api_client.get(
#         f"{API_SETTING.API_V1_STR}/permission/local-deploy",
#         headers=dummy_user_token_header,
#     )
#     assert response.status_code == 200

#     do_local_deploy_user = perm_schemas.LocalDeployUserDTO(**response.json())
#     assert do_local_deploy_user.requested_at is not None
#     assert do_local_deploy_user.approved_at is not None

#     LOCAL_DEPLOY_USER_CRUD.delete_local_deploy_user(do_local_deploy_user.id)

#     return
