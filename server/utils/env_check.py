import os

from server.settings.logger import api_logger as logger


def env_check() -> None:
    ENV_LIST = [
        "API_RUN_LOCATION",
        "DEPLOY_ENV",
        "PRODUCT_PREFIX",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_DB",
        "API_JWT_TOKEN_SECRET",
        "K8S_REDIS_PASSWORD",
        "OAUTH2_GITHUB_CLIENT_ID",
        "OAUTH2_GITHUB_CLIENT_SECRET",
        "DOMAIN_NAME",
        "IMAGE_BUILD_DATE",
        "IMAGE_TAG",
    ]

    for env in ENV_LIST:
        logger.info(f"{env} [{os.getenv(env)}]")
