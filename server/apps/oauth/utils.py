import datetime

from pydantic import EmailStr

from server.apps.oauth.crud import OAUTH_CRUD
from server.core.exception import EXCEPTION_LIB
from server.settings.logger import app_oauth_logger as logger


def verify_vcode(action: str, email: EmailStr, vcode: str) -> None:
    do_vcode = OAUTH_CRUD.get_vcode(action, email)
    if do_vcode is None:
        logger.info(
            f"[verify_vcode] The input vcode {vcode} does not exist, email {email}."
        )
        raise EXCEPTION_LIB.VCODE__CURRENT_VCODE_NOT_EXIST.value(
            f"The input vcode {vcode} is not exist"
        )

    if do_vcode.vcode != vcode:
        logger.error(
            f"[verify_vcode] The input vcode {vcode} not correct, email {email}."
        )
        raise EXCEPTION_LIB.VCODE__CURRENT_VCODE_NOT_CORRECT.value(
            f"The input vcode {vcode} is not correct! Please input it again or request a new code"
        )

    if do_vcode.expire_at < datetime.datetime.utcnow():
        logger.error(
            f"[verify_vcode] The input vcode {vcode} has been expired, email {email}."
        )
        raise EXCEPTION_LIB.VCODE__CURRENT_VCODE_EXPIRED.value(
            f"The input vcode {vcode} has been expired"
        )
