from server.settings.api_setting import APISettings
from server.settings.limitation import (
    GlobalLimitationConfig,
    UserLimitationConfig,
)

GLOBAL_LIMIT_CONFIG = GlobalLimitationConfig.load()
USER_BASE_LIMIT_CONFIG = {
    "free-user": UserLimitationConfig.load("free-user"),
    "super-user": UserLimitationConfig.load("super-user"),
}


API_SETTING = APISettings()

__all__ = ["GLOBAL_LIMIT_CONFIG", "API_SETTING", "USER_BASE_LIMIT_CONFIG"]
