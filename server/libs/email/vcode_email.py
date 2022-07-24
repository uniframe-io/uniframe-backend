from typing import Any

from server.apps.oauth.schemas import ACTION_TYPE
from server.libs.email.ses import send_email
from server.libs.email.vcode_template import (
    BODY_HTML_TEMPLATE,
    BODY_RECOVER_PASSWORD_TEMPLATE,
    BODY_SIGNUP_TEMPLATE,
    TITLE_TEMPLATE,
    VCODE_TEMPLATE,
)
from server.settings import API_SETTING


def get_subject(action: ACTION_TYPE) -> str:
    if action == ACTION_TYPE.ACTION_FORGET_PASSWORD:
        return "{product_name} Recover Password".format(
            product_name=API_SETTING.PRODUCT_NAME
        )
    else:
        return "{product_name} Email Signup".format(
            product_name=API_SETTING.PRODUCT_NAME
        )


def get_content(action: ACTION_TYPE, recipient: str, font_size: int) -> str:
    if action == ACTION_TYPE.ACTION_FORGET_PASSWORD:
        return BODY_RECOVER_PASSWORD_TEMPLATE.format(
            recipient=recipient,
            product_name=API_SETTING.PRODUCT_NAME,
            font_size=18,
        )
    else:
        return BODY_SIGNUP_TEMPLATE.format(
            recipient=recipient,
            product_name=API_SETTING.PRODUCT_NAME,
            font_size=18,
        )


def send_vcode_email(action: ACTION_TYPE, vcode: str, recipient: str) -> Any:
    subject = get_subject(action)
    title = TITLE_TEMPLATE.format(title="Verify your email", font_size=32)
    content = get_content(action, recipient, font_size=18)
    vcode = VCODE_TEMPLATE.format(vcode=vcode, font_size=40)

    body = BODY_HTML_TEMPLATE.format(title=title, content=content, vcode=vcode)

    send_email(recipient, subject, body)
