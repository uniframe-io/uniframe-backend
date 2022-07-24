from typing import Dict

from server.settings import API_SETTING


def url_gen(url: str) -> str:
    return f"{API_SETTING.HTTP_SCHEME}://{API_SETTING.COOKIE_DOMAIN}:8000{API_SETTING.API_V1_STR}/{url}"


def request_header() -> Dict:
    return {"Origin": "http://localhost"}
