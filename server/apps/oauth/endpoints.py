import datetime
import json
import os
import uuid
from datetime import timedelta
from typing import Any

import requests
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from server.apps.dataset.crud import DATASET_CRUD
from server.apps.media.crud import MEDIA_CRUD
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.oauth import schemas
from server.apps.oauth.crud import OAUTH_CRUD
from server.apps.oauth.utils import verify_vcode
from server.apps.user import schemas as user_schemas
from server.apps.user.crud import USER_CRUD
from server.core import dependency, security
from server.core.exception import EXCEPTION_LIB
from server.core.security import add_token_cookie, delete_token_cookie
from server.libs.email.vcode_email import send_vcode_email
from server.libs.fs import FILE_STORE_FACTORY
from server.settings import API_SETTING
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_oauth_logger as logger
from server.utils.vcode import digits

router = APIRouter()


@router.post(
    "/login",
    summary="Get access token by given email and password",
    response_model=schemas.Token,
    response_description="Login result",
)
def login(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    do_user = USER_CRUD.get_user_by_email(form_data.username)
    if not do_user:
        logger.error(
            f"[login] API__VALIDATE_CRDENTIALS_ERROR: email [{form_data.username}]"
        )
        raise EXCEPTION_LIB.API__VALIDATE_CRDENTIALS_ERROR.value(
            "Incorrect email"
        )

    if (
        do_user.login_type != user_schemas.LOGIN_TYPE.EMAIL
        or not do_user.hashed_password
    ):
        logger.error(
            f"[login] USER__LOGIN_TYPE_ERROR: email [{form_data.username}]"
        )
        raise EXCEPTION_LIB.USER__LOGIN_TYPE_ERROR.value(
            "You are not a registered email user. Please login with github or google."
        )

    if not security.verify_password(
        form_data.password, do_user.hashed_password
    ):
        logger.error(
            f"[login] API__VALIDATE_CRDENTIALS_ERROR: email [{form_data.username}]"
        )
        raise EXCEPTION_LIB.API__VALIDATE_CRDENTIALS_ERROR.value(
            "Incorrect password"
        )

    if not do_user.is_active:
        logger.error(f"[login] API__INACTIVE_USER: user [{do_user.id}]")
        raise EXCEPTION_LIB.API__INACTIVE_USER.value("Inactive user")

    access_token_expires = timedelta(
        minutes=API_SETTING.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = security.create_access_token(
        do_user.id, expires_delta=access_token_expires
    )

    add_token_cookie(response, access_token, request.headers.get("origin"))

    dto_user = USER_CRUD.user_do_to_dto(do_user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": dto_user.dict(),
    }


@router.post(
    "/logout",
    summary="Logout",
    response_model=str,
    response_description="current login user",
)
def logout(response: Response, request: Request) -> str:
    """
    Logout will clear cookie and redirect to login page
    """
    delete_token_cookie(response, request.headers.get("origin"))
    return "logout successfully"


@router.post(
    "/test-token",
    summary="test if current token is valid. If yes, return the current user",
    response_model=user_schemas.UserDTO,
    response_description="current user",
)
def test_token(
    current_user: user_schemas.UserDO = Depends(
        dependency.get_current_active_user
    ),
) -> Any:
    """
    Test access token
    """
    return USER_CRUD.user_do_to_dto(current_user)


# @router.post("/password-recovery/{email}", response_model=schemas.Msg)
# def recover_password(email: str) -> Any:
#     """
#     Password Recovery
#     """
#     user = models.user_model.get_user_by_email(email=email)

#     if not user:
#         raise HTTPException(
#             status_code=404,
#             detail="The user with this username does not exist in the system.",
#         )
#     password_reset_token = generate_password_reset_token(email=email)
#     send_reset_password_email(
#         email_to=user.email, email=email, token=password_reset_token
#     )
#     return {"msg": "Password recovery email sent"}


@router.post(
    "/signup",
    summary="Create an account by given email, full_name and email",
    response_model=str,
    response_description="Sign up successful message",
)
def signup(
    *, user_create: user_schemas.UserCreateDTO, response: Response
) -> str:
    """
    Create a new user by given email, full_name and email then return access token.

    Input schema: **UserCreateDTO**
    - email: login email
    - full_name: full name of a user
    - password: user password
    - vcode: vcode get from email
    """
    logger.info(f"sign-in verify vcode: [{os.getenv('API_RUN_LOCATION')}]")
    if os.getenv("API_RUN_LOCATION") not in ["test", "local", "minikube"]:
        verify_vcode(
            schemas.ACTION_TYPE.ACTION_SIGNUP,
            user_create.email,
            user_create.vcode,
        )

    do_user = USER_CRUD.get_user_by_email(user_create.email)
    if do_user is not None:
        logger.error(
            f"[signup] USER__EMAIL_ALREADY_EXISTS: email [{user_create.email}]"
        )
        raise EXCEPTION_LIB.USER__EMAIL_ALREADY_EXISTS.value(
            f"The email {user_create.email} already exists in the system"
        )

    do_user_create = user_schemas.UserCreateDO(
        email=user_create.email,
        hashed_password=security.get_password_hash(user_create.password),
        full_name=user_create.full_name,
        login_type=user_schemas.LOGIN_TYPE.EMAIL,
    )
    do_user = USER_CRUD.create_user(do_user_create)

    OAUTH_CRUD.delete_vcode_by_action(
        schemas.ACTION_TYPE.ACTION_SIGNUP, user_create.email
    )

    # N.B. sign up will not return anything for now!
    # access_token_expires = timedelta(
    #     minutes=API_SETTING.ACCESS_TOKEN_EXPIRE_MINUTES
    # )
    # access_token = security.create_access_token(
    #     do_user.id, expires_delta=access_token_expires
    # )

    # set_token_cookie(response, access_token)

    # return USER_CRUD.user_do_to_dto(do_user)
    return "Sign-up successfully"


@router.post(
    "/reset-password",
    summary="Reset password by given new password",
    response_model=str,
    response_description="response message of reset password",
)
def reset_password(
    *,
    response: Response,
    request: Request,
    current_user: user_schemas.UserDO = Depends(
        dependency.get_current_active_user
    ),
    user_reset_password: user_schemas.UserResetPasswordDTO,
) -> str:
    """
    Reset password by given new password, validate old password before reset.

    Input schema: **UserResetPasswordDTO**
    - old_password: old password
    - new_password: new password
    """
    if user_reset_password.old_password == user_reset_password.new_password:
        logger.error(
            f"[reset_password] USER__RESET_PASSWORD_ERROR: current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.USER__RESET_PASSWORD_ERROR.value(
            "The new password needs to be different from the old one"
        )

    if (
        current_user.login_type != user_schemas.LOGIN_TYPE.EMAIL
        or not current_user.hashed_password
    ):
        logger.error(
            f"[reset_password] USER__LOGIN_TYPE_ERROR: login type [{user_schemas.LOGIN_TYPE.EMAIL}]"
            f" current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.USER__LOGIN_TYPE_ERROR.value(
            "You are not a registered email user and you can not reset password."
        )

    if not security.verify_password(
        user_reset_password.old_password, current_user.hashed_password
    ):
        logger.error(
            f"[reset_password] API__VALIDATE_CRDENTIALS_ERROR: current_user [{current_user.id}]"
        )
        raise EXCEPTION_LIB.API__VALIDATE_CRDENTIALS_ERROR.value(
            "Incorrect password"
        )

    hashed_password = security.get_password_hash(
        user_reset_password.new_password
    )

    do_user_update = user_schemas.UserUpdateDO(hashed_password=hashed_password)
    USER_CRUD.update_user(current_user.id, do_user_update)

    delete_token_cookie(response, request.headers.get("origin"))
    return "Password updated successfully"


@router.post(
    "/deactivate",
    summary="Deactivate account",
    response_model=str,
    response_description="Response message of deactivate",
)
def deactivate(
    *,
    response: Response,
    request: Request,
    current_user: user_schemas.UserDO = Depends(
        dependency.get_current_active_user
    ),
) -> str:
    """
    Deactivate account

    The current decision is that we will keeps the records in all tables and only
    delete s3 data (or local data in local testing or minikube version).

    The steps are:
    In user table, set is_active as False. Replace full_name field
    by “deactive_user” + uuid, replace email by “uuid@deactive-user.com”

    Iterate all media files the user have. Delete all files on s3 or local
    file system physically. Replace media record ext_info field by “deleted” text

    oauth2_user record:
    Replace ext_info field in oauth2_user record by “delete” text, because
    oauthe2_user ext_info field contains personal informaiton there, setup is_active as False

    In media, dataset, task tables, set is_active field as False
    """

    # Here we put update_user fist is to prevent unknown bugs between two transactions.
    # If the user open two tabs in browser, execute deactivate account in tab A and meanwhile
    # execute run task or edit dataset in tab B. If we put update_user to the end, because the
    # status of the user is active and also the task, so he can execute run task but maybe the
    # media of the task is deleted at the same time in transaction A. In that case transaction
    # B will cause some unknown bugs. So here put update_user first is a better choice.
    uuid_str = str(uuid.uuid4())
    do_user_update = user_schemas.UserUpdateDO(
        is_active=False,
        full_name="deactive_user",
        email=f"{uuid_str}@deactive-user.com",
    )
    USER_CRUD.update_user(current_user.id, do_user_update)
    if current_user.login_type != user_schemas.LOGIN_TYPE.EMAIL:
        OAUTH_CRUD.update_oauth2_user(
            current_user.id,
            schemas.OAuth2UserUpdateDO(is_active=False, ext_info="deleted"),
        )

    NM_TASK_CRUD.delete_task_by_owner(current_user.id)
    active_datasets = DATASET_CRUD.get_datasets_by_owner(current_user.id)

    if len(active_datasets) > 0:
        DATASET_CRUD.delete_dataset_by_owner(current_user.id)
        active_dataset_ids = [d.id for d in active_datasets]
        DATASET_CRUD.delete_public_dataset_by_ids(active_dataset_ids)

    MEDIA_CRUD.delete_media_by_owner(current_user.id)

    user_all_medias = MEDIA_CRUD.get_all_medias_by_owner(current_user.id)
    bucket_name = GLOBAL_CONFIG.bucket_name
    for m in user_all_medias:
        # local: /app/localfs/uniframe-local-data/user=718012433/medias/5953ce62-086e-4102-9d8c-ba97498b034c
        # dev/prod: s3://uniframe-dev-data/user=1111111111/medias/a19ae5a4-6c66-4f5a-b85d-asdfxzcvadsf
        key_name = m.location.split(bucket_name)[1][1:]
        FILE_STORE_FACTORY.delete_object(
            bucket_name=bucket_name, key_name=key_name
        )

    delete_token_cookie(response, request.headers.get("origin"))
    return "Deactivate account successfully"


def get_github_user_info(access_token: str) -> dict:
    """
    Get github user info
    """
    user_url = "https://api.github.com/user"
    access_token = "token {}".format(access_token)
    headers = {"accept": "application/json", "Authorization": access_token}
    res = requests.get(user_url, headers=headers)
    if res.status_code != 200:
        logger.error(
            f"[oauth2_github_redirect] OAUTH2__GITHUB_REQUEST_ERROR: get user info error access_token [{res.json()}]"
        )
        raise EXCEPTION_LIB.OAUTH2__GITHUB_REQUEST_ERROR.value(
            "github oauth2 get user info error"
        )

    user_info = res.json()
    return user_info


def get_github_token(code: str) -> str:
    """
    Exchange code for an access token
    """
    token_url = (
        "https://github.com/login/oauth/access_token?"
        "client_id={}&client_secret={}&code={}"
    )
    token_url = token_url.format(
        API_SETTING.OAUTH2_GITHUB_CLIENT_ID,
        API_SETTING.OAUTH2_GITHUB_CLIENT_SECRET,
        code,
    )
    header = {"accept": "application/json"}
    res = requests.post(token_url, headers=header)
    if res.status_code != 200:
        logger.error(
            f"[oauth2_github_redirect] OAUTH2__GITHUB_REQUEST_ERROR: github oauth2 code exchange token error res [{res.json()}]"
        )
        raise EXCEPTION_LIB.OAUTH2__GITHUB_REQUEST_ERROR.value(
            "github oauth2 code exchange token error"
        )

    res_dict = res.json()
    access_token = res_dict.get("access_token")
    if not access_token:
        logger.error(
            f"[oauth2_github_redirect] OAUTH2__GITHUB_REQUEST_ERROR: res [{res.json()}]"
        )
        raise EXCEPTION_LIB.OAUTH2__GITHUB_REQUEST_ERROR.value(
            "access_token not in response"
        )

    return access_token


@router.get("/oauth2/github/redirect", response_class=RedirectResponse)
def oauth2_github_redirect(request: Request) -> RedirectResponse:
    """
    Sign in with Github
    """
    code = request.query_params.get("code")
    provider_token = get_github_token(code)

    user_info = get_github_user_info(provider_token)

    github_id = user_info.get("id")
    username = user_info.get("login")

    if not github_id or not username:
        logger.error(
            f"[oauth2_github_redirect] OAUTH2__GITHUB_REQUEST_USER_ERROR: github user info error token [{provider_token}]"
        )
        raise EXCEPTION_LIB.OAUTH2__GITHUB_REQUEST_USER_ERROR.value(
            "request github user info error"
        )

    access_token_expires = timedelta(
        minutes=API_SETTING.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    do_oauth2_user = OAUTH_CRUD.get_oauth2_user(
        schemas.OAUTH2_PROVIDER_TYPE.PROVIDER_GITHUB, github_id
    )
    if do_oauth2_user is not None:
        access_token = security.create_access_token(
            do_oauth2_user.owner_id, expires_delta=access_token_expires
        )

        response = RedirectResponse(
            url=f"{API_SETTING.HTTP_SCHEME}://{API_SETTING.COOKIE_DOMAIN}/"
        )
        add_token_cookie(response, access_token)

        return response

    oauth2_user_create = schemas.OAuth2UserCreateDO(
        provider=schemas.OAUTH2_PROVIDER_TYPE.PROVIDER_GITHUB,
        provider_id=github_id,
        ext_info=json.dumps(user_info),
        full_name=username,
        login_type=user_schemas.LOGIN_TYPE.OAUTH2_GITHUB,
    )
    email = user_info.get("email")
    if email:
        oauth2_user_create.email = email

    do_oauth2_user = OAUTH_CRUD.create_oauth2_user(oauth2_user_create)

    access_token = security.create_access_token(
        do_oauth2_user.owner_id, expires_delta=access_token_expires
    )

    response = RedirectResponse(
        url=f"{API_SETTING.HTTP_SCHEME}://{API_SETTING.COOKIE_DOMAIN}/"
    )
    add_token_cookie(response, access_token)

    return response


@router.post(
    "/vcode/send",
    summary="Send verification code",
    response_model=str,
    response_description="Response message of sending verification code",
)
def vcode_send(
    *,
    vcode_send: schemas.VCodeSendDTO,
) -> str:
    """
    Send verification code to the input email.

    Input schema: **VCodeSendDTO**
    - email: email that the verification code sent to
    - action: forget_password or signup
    """
    if vcode_send.action not in (
        schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD,
        schemas.ACTION_TYPE.ACTION_SIGNUP,
    ):
        logger.error(
            f"[vcode_send] The input action type {vcode_send.action} error, email {vcode_send.email}"
        )
        raise EXCEPTION_LIB.VCODE__ACTION_TYPE_ERROR.value(
            f'The input action type {vcode_send.action} error, please use "{schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD.value}" or "{schemas.ACTION_TYPE.ACTION_SIGNUP.value}"'
        )

    do_user = USER_CRUD.get_user_by_email(vcode_send.email)
    if (
        vcode_send.action == schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD
        and do_user is None
    ):
        logger.error(
            f"[vcode_send] The input email {vcode_send.email} is not a registered email"
        )
        raise EXCEPTION_LIB.USER__EMAIL_NOT_EXISTS.value(
            f"The input email {vcode_send.email} is not a registered email"
        )

    if vcode_send.action == schemas.ACTION_TYPE.ACTION_SIGNUP and do_user:
        logger.error(
            f"[vcode_send] The input email {vcode_send.email} already been registered."
        )
        raise EXCEPTION_LIB.USER__EMAIL_NOT_EXISTS.value(
            f"The input email {vcode_send.email} already been registered, please use another email."
        )

    cnt = OAUTH_CRUD.get_vcode_count(vcode_send.email, vcode_send.action)
    if cnt > API_SETTING.VCODE_DAY_LIMIT:
        logger.error(
            f"[vcode_send] The count of the input action type {vcode_send.action} excceed limit for email {vcode_send.email}."
        )
        raise EXCEPTION_LIB.VCODE__EXCCEED_LIMIT.value(
            "The number of verification codes your requested has exceed the daily limit. Please try it in 1 hours"
        )

    # TODO add checking wrong vcode count in future

    vcode = digits(API_SETTING.VCODE_DIGIT, str)

    vcode_create_do = schemas.VerificationCodeCreateDO(
        email=vcode_send.email,
        action=vcode_send.action,
        vcode=vcode,
        expire_at=datetime.datetime.utcnow()
        + timedelta(minutes=API_SETTING.VCODE_EXPIRE_MINUTE),
    )
    OAUTH_CRUD.create_vcode(vcode_create_do)

    send_vcode_email(vcode_send.action, vcode, vcode_send.email)

    return "Verification code sent successfully"


@router.post(
    "/vcode/verify",
    summary="Verify the input verification code",
    response_model=str,
    response_description="Response message of verifing the input verification code",
)
def vcode_verify(
    *,
    vcode: schemas.VCodeVerifyDTO,
) -> str:
    """
    Verify the input verification code according to the input action type.

    Input schema: **VCodeVerifyDTO**
    - email: email that the verification code sent to
    - action: forget_password or signup
    - vcode: vcode get from email
    """
    if vcode.action not in (
        schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD,
        schemas.ACTION_TYPE.ACTION_SIGNUP,
    ):
        logger.error(
            f"[vcode_verify] The input action type {vcode_verify.action} error, email {vcode.email}."
        )
        raise EXCEPTION_LIB.VCODE__ACTION_TYPE_ERROR.value(
            f'The input action type {vcode.action} error, please use "{schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD.value}" or "{schemas.ACTION_TYPE.ACTION_SIGNUP.value}"'
        )

    do_user = USER_CRUD.get_user_by_email(vcode.email)
    if (
        vcode.action == schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD
        and do_user is None
    ):
        logger.error(
            f"[vcode_verify] The input email {vcode.email} is not a registered email."
        )
        raise EXCEPTION_LIB.USER__EMAIL_NOT_EXISTS.value(
            f"The input email {vcode.email} is not a registered email"
        )

    if vcode.action == schemas.ACTION_TYPE.ACTION_SIGNUP and do_user:
        logger.error(
            f"[vcode_verify] The input email {vcode.email} already been registered."
        )
        raise EXCEPTION_LIB.USER__EMAIL_NOT_EXISTS.value(
            f"The input email {vcode.email} already been registered, please use another email."
        )

    verify_vcode(vcode.action, vcode.email, vcode.vcode)
    return "vcode verified successfully"


@router.post(
    "/password/recover",
    summary="Recover password",
    response_model=str,
    response_description="Response message of recover password",
)
def password_recover(
    *,
    password_recover: schemas.PasswordRecoverDTO,
) -> str:
    """
    Recover password

    Input schema: **PasswordRecoverDTO**
    - email: email that the verification code sent to
    - vcode: vcode get from email
    - new: new passwrod
    """
    do_user = USER_CRUD.get_user_by_email(password_recover.email)
    if do_user is None:
        logger.error(
            f"[password_recover] The input email {password_recover.email} is not a registered email."
        )
        raise EXCEPTION_LIB.USER__EMAIL_NOT_EXISTS.value(
            f"The input email {password_recover.email} is not a registered email"
        )

    verify_vcode(
        schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD,
        password_recover.email,
        password_recover.vcode,
    )
    hashed_password = security.get_password_hash(password_recover.new)

    do_user_update = user_schemas.UserUpdateDO(hashed_password=hashed_password)
    USER_CRUD.update_user(do_user.id, do_user_update)

    OAUTH_CRUD.delete_vcode_by_action(
        schemas.ACTION_TYPE.ACTION_FORGET_PASSWORD, password_recover.email
    )

    return "Password updated successfully"
