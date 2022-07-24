from typing import List, Optional

from fastapi import APIRouter, Depends

from server.apps.dataset import utils as dataset_utils
from server.apps.dataset.crud import DATASET_CRUD
from server.apps.user.crud import USER_CRUD
from server.apps.user.schemas import (
    LOGIN_TYPE,
    UserCreateDO,
    UserCreateDTO,
    UserDO,
    UserDTO,
)
from server.core import dependency, security
from server.core.exception import EXCEPTION_LIB
from server.settings.logger import app_user_logger as logger

router = APIRouter()


def get_shared_users(
    action: str, resource_type: str, query: int, current_user: UserDO
) -> List[UserDTO]:
    """
    Get users shared with dataset
    """
    if action != "shared" and resource_type != "dataset":
        return []

    if not query:
        return []

    do_dataset = DATASET_CRUD.get_dataset(query)
    if do_dataset is None:
        return []

    have_access, ownership_type = dataset_utils.check_access(
        do_dataset, current_user
    )
    if not have_access:
        logger.error(
            f"[list_users] DATASET__CURRENT_USER_HAS_NO_PERMISSION: do dataset [{do_dataset.id}] current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.DATASET__CURRENT_USER_HAS_NO_PERMISSION.value(
            "You are not allowed to get current dataset."
        )

    user_ids = DATASET_CRUD.get_shared_users(query)

    do_users = USER_CRUD.get_user_by_ids(user_ids)

    return [USER_CRUD.user_do_to_dto(do_user) for do_user in do_users]


@router.get(
    "/users",
    summary="Get users",
    response_model=List[UserDTO],
    response_description="A list of active users",
)
def list_users(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    query: Optional[int] = None,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> List[UserDTO]:
    """
    Retrieve users. Two scenarios are supported for now

    1. Get all users if current user is a superuser
    2. Get users that shared with dataset

    - action: shared
    - resource_type: dataset
    - query: dataset id
    - current_user: logged-in user
    """

    if action:
        if not resource_type or not query:
            return []
        return get_shared_users(action, resource_type, query, current_user)

    if not current_user.is_superuser:
        logger.error(
            f"[list_users] API__NO_ENOUGH_PRIVILEGE: current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.API__NO_ENOUGH_PRIVILEGE.value(
            "The user doesn't have enough privileges. A super user is required"
        )

    users = USER_CRUD.get_all_users()
    return [USER_CRUD.user_do_to_dto(do_user) for do_user in users]


@router.post(
    "/users",
    summary="Create a new user",
    response_model=UserDTO,
    response_description="Created user",
)
def create_user(
    *,
    user_create: UserCreateDTO,
    current_user: UserDO = Depends(dependency.get_current_active_superuser),
) -> UserDTO:
    """
    Create a new user, only super user is allowed for this endpoint

    Input schema: **UserCreateDTO**
    - email: login email
    - full_name: full name of a user
    - password: user password
    """

    do_user = USER_CRUD.get_user_by_email(user_create.email)
    if do_user is not None:
        logger.error(
            f"[create_user] USER__EMAIL_ALREADY_EXISTS: email [{user_create.email}]"
        )
        raise EXCEPTION_LIB.USER__EMAIL_ALREADY_EXISTS.value(
            f"The email {user_create.email} already exists in the system"
        )

    do_user_create = UserCreateDO(
        email=user_create.email,
        hashed_password=security.get_password_hash(user_create.password),
        full_name=user_create.full_name,
        login_type=LOGIN_TYPE.EMAIL,
    )
    do_user = USER_CRUD.create_user(do_user_create)
    # TODO: send email? see issue #68
    return USER_CRUD.user_do_to_dto(do_user)
