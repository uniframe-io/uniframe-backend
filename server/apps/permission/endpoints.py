import datetime
from datetime import timedelta
from typing import Optional

import boto3
from fastapi import APIRouter, Depends

from server.apps.permission.crud import LOCAL_DEPLOY_USER_CRUD
from server.apps.permission.schemas import (
    AwsSessionToken,
    LocalDeployUserCreateDO,
    LocalDeployUserCreateDTO,
    LocalDeployUserDO,
    LocalDeployUserDTO,
)
from server.apps.user.schemas import UserDO
from server.core import dependency
from server.core.exception import EXCEPTION_LIB
from server.libs.email.ses import send_email
from server.libs.email.vcode_template import (
    BODY_HTML_TEMPLATE,
    CONTENT_TEMPLATE,
    TITLE_TEMPLATE,
)
from server.settings import API_SETTING
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_permission_logger as logger
from server.utils.aws_helper import id_gen

router = APIRouter()

# TODO: chagne hardcoded region name to environment variable
# This endpoint group only works for call only works for
ssm_client = boto3.client("ssm", region_name=GLOBAL_CONFIG.region.value)
sts_client = boto3.client("sts", region_name=GLOBAL_CONFIG.region.value)


def notify_admin(do_local_deploy_user: LocalDeployUserDO) -> None:
    """
    Send email to UniFrame admin
    """
    subject = f"{API_SETTING.PRODUCT_NAME} Local Deployment Request Company [{do_local_deploy_user.company}] [{do_local_deploy_user.email}]"

    title = TITLE_TEMPLATE.format(
        title=f"{API_SETTING.PRODUCT_NAME} Local Deployment Request",
        font_size=24,
    )

    content_txt = f"""
    <ul>
    <li>id: {do_local_deploy_user.id}</li>
    <li>email: {do_local_deploy_user.email}</li>
    <li>user_id: {do_local_deploy_user.user_id}</li>
    <li>company: {do_local_deploy_user.company}</li>
    <li>role: {do_local_deploy_user.role}</li>
    <li>purpose: {do_local_deploy_user.purpose}</li>
    <li>requested_at: {do_local_deploy_user.requested_at}</li>
    </ul>
    """
    content = CONTENT_TEMPLATE.format(txt=content_txt, font_size=18)

    body = BODY_HTML_TEMPLATE.format(title=title, content=content, vcode="")

    send_email(recipient="info@uniframe.io", subject=subject, body=body)


def notify_user(do_local_deploy_user: LocalDeployUserDO) -> None:
    """
    Send email to local deployment request user
    """
    # TODO: add tutorial link
    subject = f"{API_SETTING.PRODUCT_NAME} Local Deployment Request Apporved"

    title = TITLE_TEMPLATE.format(
        title=f"{API_SETTING.PRODUCT_NAME} Local Deployment Request Approved",
        font_size=24,
    )

    content_txt = """
    Your local deployment request at {datetime} has been approved. Please visit our website uniframe.io, and follow this tutorial [link] for local deployment.
    """.format(
        datetime=do_local_deploy_user.requested_at
    )
    content = CONTENT_TEMPLATE.format(txt=content_txt, font_size=18)

    body = BODY_HTML_TEMPLATE.format(title=title, content=content, vcode="")

    send_email(recipient=do_local_deploy_user.email, subject=subject, body=body)


@router.post(
    "/permission/local-deploy/request",
    summary="Request UniFrame local deployment permission",
    response_model=str,
    response_description="response message",
)
def request_local_deploy(
    req_info: LocalDeployUserCreateDTO,
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> str:
    do_local_deploy_user = LOCAL_DEPLOY_USER_CRUD.get_local_deploy_user(
        current_user.id
    )

    if do_local_deploy_user is not None:
        logger.error(
            f"[/permission/local-deploy/request] LOCAL_DEPLOY__REQUEST_ALREADY_EXISTS: user_id [{current_user.id}]"
        )
        raise EXCEPTION_LIB.LOCAL_DEPLOY__REQUEST_ALREADY_EXISTS.value(
            "You have already applys local deployment before. Please wait for admin approve or renew the request. Please contact info@uniframe.io if you have any question"
        )

    # create a new local deployment request
    do_local_deploy_user_create = LocalDeployUserCreateDO(
        email=current_user.email,
        user_id=current_user.id,
        company=req_info.company,
        role=req_info.role,
        purpose=req_info.purpose,
    )
    do_local_deploy_user = LOCAL_DEPLOY_USER_CRUD.create_local_deploy_user(
        do_local_deploy_user_create
    )

    notify_admin(do_local_deploy_user)

    return "Local deployment request successfully"


@router.get(
    "/permission/local-deploy",
    summary="Get the local deploy request information",
    response_model=LocalDeployUserDTO,
    response_description="Local deployment request information",
)
def get_local_deploy(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> Optional[LocalDeployUserDTO]:
    """
    Retrieve local deployment request information
    """
    do_local_deploy_user = LOCAL_DEPLOY_USER_CRUD.get_local_deploy_user(
        current_user.id
    )

    if do_local_deploy_user is None:
        return None

    dto_local_deploy_user = LocalDeployUserDTO(
        id=do_local_deploy_user.id,
        company=do_local_deploy_user.company,
        role=do_local_deploy_user.role,
        purpose=do_local_deploy_user.purpose,
        requested_at=do_local_deploy_user.requested_at,
        approved_at=do_local_deploy_user.approved_at,
        expire_at=do_local_deploy_user.expire_at,
    )

    return dto_local_deploy_user


def renew_local_deploy_perm(user_id: int) -> None:
    do_local_deploy_user = LOCAL_DEPLOY_USER_CRUD.get_local_deploy_user(user_id)

    if do_local_deploy_user is None:
        logger.error(
            f"[/permission/local-deploy/{user_id}/approve] LOCAL_DEPLOY__REQUEST_NOT_EXISTS: request from user_id [{user_id}] not exist"
        )
        raise EXCEPTION_LIB.LOCAL_DEPLOY__REQUEST_NOT_EXISTS.value(
            "User_id {user_id} local deploy request does not exist"
        )

    do_local_deploy_user.is_active = True
    do_local_deploy_user.approved_at = datetime.datetime.utcnow()
    do_local_deploy_user.expire_at = datetime.datetime.utcnow() + timedelta(
        days=30
    )

    LOCAL_DEPLOY_USER_CRUD.update_local_deploy_user(do_local_deploy_user)

    notify_user(do_local_deploy_user)


@router.post(
    "/permission/local-deploy/{user_id}/approve",
    summary="Approve the local deploy request by admin user",
    response_model=str,
    response_description="Approve Local deployment request information",
)
def approve_local_deploy(
    user_id: int,
    super_user: UserDO = Depends(dependency.get_current_active_superuser),
) -> str:
    """
    Approve local deployment request information
    """
    renew_local_deploy_perm(user_id)

    return "Approve local deploy request successfully"


@router.post(
    "/permission/local-deploy/{user_id}/renew",
    summary="Approve the local deploy request by admin user",
    response_model=str,
    response_description="Approve Local deployment request information",
)
def renew_local_deploy(
    user_id: int,
    super_user: UserDO = Depends(dependency.get_current_active_superuser),
) -> str:
    """
    Approve local deployment request information
    """
    renew_local_deploy_perm(user_id)

    return "Renew local deploy request successfully"


@router.get(
    "/permission/local-deploy/request-token",
    summary="Get the temporary token to pull ECR image",
    response_model=AwsSessionToken,
    response_description="temporary token",
)
def get_ECR_temporary_token(
    current_user: UserDO = Depends(dependency.get_current_active_user),
) -> AwsSessionToken:
    """
    Retrieve local deployment request information
    """
    user_id = current_user.id

    do_local_deploy_user = LOCAL_DEPLOY_USER_CRUD.get_local_deploy_user(
        current_user.id
    )

    if do_local_deploy_user is None:
        logger.error(
            f"[/permission/local-deploy/request-token] LOCAL_DEPLOY__REQUEST_NOT_EXISTS: request from user_id [{user_id}] not exist"
        )
        raise EXCEPTION_LIB.LOCAL_DEPLOY__REQUEST_NOT_EXISTS.value(
            "You have not request local deploy yet"
        )

    if (
        not do_local_deploy_user.is_active
        or do_local_deploy_user.expire_at is None
    ):
        logger.error(
            f"[/permission/local-deploy/request-token] LOCAL_DEPLOY__REQUEST_NOT_APPROVED: request of [{user_id}] has not been approved yet"
        )
        raise EXCEPTION_LIB.LOCAL_DEPLOY__REQUEST_NOT_EXISTS.value(
            "Your local deployment request has not been approved by the admin yet. Please wait or contact us"
        )

    if do_local_deploy_user.expire_at < datetime.datetime.utcnow():
        logger.error(
            f"[/permission/local-deploy/request-token] LOCAL_DEPLOY__APPROVAL_EXPIRED: approval of [{user_id}] has been expired"
        )
        raise EXCEPTION_LIB.LOCAL_DEPLOY__APPROVAL_EXPIRED.value(
            "Your local deployment approval has been expired. One request lasts for 30 days. Please renew your request"
        )

    # Get ecr-readonly-role
    ssm_parameter_name = id_gen("ssm-ecr-readonly-role")
    ecr_readonly_role_arn = ssm_client.get_parameter(Name=ssm_parameter_name)[
        "Parameter"
    ]["Value"]

    # assume role
    response = sts_client.assume_role(
        RoleArn=ecr_readonly_role_arn,
        RoleSessionName="local-user-pull-ecr-image-session",
    )
    return AwsSessionToken(
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
    )
