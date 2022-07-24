from typing import Dict

from fastapi import APIRouter, Depends

from server.apps.config.schemas import HelpGuide
from server.apps.nm_task.schemas import NmTaskCreateDTO
from server.apps.user.schemas import UserDO
from server.apps.user.utils import get_user_premium_type
from server.core import dependency
from server.settings import GLOBAL_LIMIT_CONFIG, USER_BASE_LIMIT_CONFIG
from server.settings.limitation import NmTaskResourceLimit, UserUIPermission
from server.utils.parser import load_json, load_yaml

router = APIRouter()


@router.get(
    "/config/defaults/nm/batch",
    summary="Get default values for creating name matching batch task",
    response_model=NmTaskCreateDTO,
    response_description="the name matching batch task default value",
)
def get_nm_batch_task_defaults(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> NmTaskCreateDTO:
    cfg_dict = load_yaml("./conf/nm-task-batch-default.yaml")
    return NmTaskCreateDTO(**cfg_dict)


@router.get(
    "/config/defaults/nm/real-time",
    summary="Get default values for creating name matching realtime task",
    response_model=NmTaskCreateDTO,
    response_description="the name matching realtime task default value",
)
def get_nm_rt_task_defaults(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> NmTaskCreateDTO:
    cfg_dict = load_yaml("./conf/nm-task-rt-default.yaml")
    return NmTaskCreateDTO(**cfg_dict)


@router.get(
    "/config/help-guide",
    summary="Get help guide which is shown in the website",
    response_model=Dict[str, HelpGuide],
    response_description="Help guide",
)
def get_help_guide(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> Dict[str, HelpGuide]:
    help_guide_dict = load_json("./conf/help-guide.json")
    return help_guide_dict


@router.get(
    "/config/nm-task-cpu-mem-limit",
    summary="Get name matching task cpu and memory limitation",
    response_model=Dict[str, NmTaskResourceLimit],
    response_description="the resource limitation of name matching task",
)
def get_nm_task_resource_limit(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> Dict[str, NmTaskResourceLimit]:
    return GLOBAL_LIMIT_CONFIG.task_pod_cfg


@router.get(
    "/config/get-ui-permission",
    summary="Get user UI permission",
    response_model=UserUIPermission,
    response_description="the UI permission of current user",
)
def get_user_ui_permission(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> UserUIPermission:
    user_permium_type = get_user_premium_type(current_user)
    ui_permission = USER_BASE_LIMIT_CONFIG[user_permium_type].ui_permission

    return ui_permission
