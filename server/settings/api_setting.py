import os
import secrets

from pydantic import (  # AnyHttpUrl,; EmailStr,; HttpUrl,; PostgresDsn,; validator,
    BaseSettings,
)

from server.settings.global_sys_config import GLOBAL_CONFIG


# Copy from https://github.com/tiangolo/full-stack-fastapi-postgresql/blob/490c554e23343eec0736b06e59b2108fdd057fdc/%7B%7Bcookiecutter.project_slug%7D%7D/backend/app/app/core/config.py
# TODO: refine the APISettings
class APISettings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv(
        "API_JWT_TOKEN_SECRET", secrets.token_urlsafe(32)
    )
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    HTTP_SCHEME: str = (
        "http"
        if os.getenv("API_RUN_LOCATION") in ["local", "test", "minikube"]
        else "https"
    )
    # SERVER_NAME: str
    # SERVER_HOST: AnyHttpUrl
    # # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    # BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # @validator("BACKEND_CORS_ORIGINS", pre=True)
    # def assemble_cors_origins(
    #     cls, v: Union[str, List[str]]
    # ) -> Union[List[str], str]:
    #     if isinstance(v, str) and not v.startswith("["):
    #         return [i.strip() for i in v.split(",")]
    #     elif isinstance(v, (list, str)):
    #         return v
    #     raise ValueError(v)

    # PROJECT_NAME: str
    # SENTRY_DSN: Optional[HttpUrl] = None

    # @validator("SENTRY_DSN", pre=True)
    # def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
    #     if len(v) == 0:
    #         return None
    #     return v

    SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
    SQLALCHEMY_DATABASE_LOCAL_URL = "postgresql://postgres:postgres@db/nm"
    SQLALCHEMY_DATABASE_MINIKUBE_URL = (
        "postgresql://postgres:postgres@postgresql/nm"
    )
    SQLALCHEMY_DATABASE_PYTEST_URL = "postgresql://postgres:postgres@db/test_nm"
    SQLALCHEMY_DATABASE_DEFAULT_URL = (
        "postgresql://postgres:postgres@db/postgres"
    )
    # SQLALCHEMY_DATABASE_TEST_URL = "postgresql://postgres:postgres@db/test_nm"

    REDIS_DNS_LOCAL = "rq_redis"
    REDIS_DNS_ECS = "localhost"
    REDIS_DNS_K8S = "redis-master.nm.svc.cluster.local"
    REDIS_DNS = (
        REDIS_DNS_LOCAL
        if os.getenv("API_RUN_LOCATION") in ["local", "test"]
        else REDIS_DNS_K8S
        if os.getenv("API_RUN_LOCATION") in ["k8s", "minikube"]
        else REDIS_DNS_ECS
    )

    REALTIME_NM_ENDPOINT_URL_LOCAL = "rq_worker_realtime"
    REALTIME_NM_ENDPOINT_URL_ECS = "localhost"
    REALTIME_NM_ENDPOINT_URL = (
        REALTIME_NM_ENDPOINT_URL_LOCAL
        if os.getenv("API_RUN_LOCATION") in ["local", "test"]
        else REALTIME_NM_ENDPOINT_URL_ECS
    )
    REALTIME_NM_ENDPOINT_PORT = "8002"

    # How OAUTH2_GITHUB_CLIENT_ID and OAUTH2_GITHUB_CLIENT_SECRET set:
    # - setup in AWS secret manager
    # - in EKS version, load from secret manager and set in ENV
    # - in docker-compose and minikube, use a dummy value
    OAUTH2_GITHUB_CLIENT_ID = os.getenv("OAUTH2_GITHUB_CLIENT_ID")
    OAUTH2_GITHUB_CLIENT_SECRET = os.getenv("OAUTH2_GITHUB_CLIENT_SECRET")

    COOKIE_DOMAIN = os.getenv("DOMAIN_NAME")

    VCODE_EXPIRE_MINUTE = 10
    VCODE_DAY_LIMIT = 5
    VCODE_DIGIT = 6
    PRODUCT_NAME = "UniFrame"

    LOCALFS_VOLUME_LOCATION = GLOBAL_CONFIG.localfs_volume_loc

    ROUTER_LOOGER_SKIP_ROUTES = ["/health-check", "/metrics"]

    # demo account is public for everyone
    DEMO_ACCOUNT_LIMITATION: bool = False
    DEMO_ACCOUNT_EMAIL: str = "info+demo@uniframe.io"
    DEMO_ACCOUNT_GET_DISABLE_PATH = ["/api/v1/users"]

    OPS_ACCOUNT_EMAIL: str = "info+ops@uniframe.io"

    X_RAPIDAPI_PROXY_SECRET: str = os.getenv(
        "RAPIDAPI_PROXY_SECRET", secrets.token_urlsafe(32)
    )

    # @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    # def assemble_db_connection(
    #     cls, v: Optional[str], values: Dict[str, Any]
    # ) -> Any:
    #     if isinstance(v, str):
    #         return v
    #     return PostgresDsn.build(
    #         scheme="postgresql",
    #         user=values.get("POSTGRES_USER"),
    #         password=values.get("POSTGRES_PASSWORD"),
    #         host=values.get("POSTGRES_SERVER"),
    #         path=f"/{values.get('POSTGRES_DB') or ''}",
    #     )

    # SMTP_TLS: bool = True
    # SMTP_PORT: Optional[int] = None
    # SMTP_HOST: Optional[str] = None
    # SMTP_USER: Optional[str] = None
    # SMTP_PASSWORD: Optional[str] = None
    # EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    # EMAILS_FROM_NAME: Optional[str] = None

    # @validator("EMAILS_FROM_NAME")
    # def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:
    #     if not v:
    #         return values["PROJECT_NAME"]
    #     return v

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    # EMAIL_TEMPLATES_DIR: str = "/app/app/email-templates/build"
    # EMAILS_ENABLED: bool = False

    # @validator("EMAILS_ENABLED", pre=True)
    # def get_emails_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:
    #     return bool(
    #         values.get("SMTP_HOST")
    #         and values.get("SMTP_PORT")
    #         and values.get("EMAILS_FROM_EMAIL")
    #     )

    # EMAIL_TEST_USER: EmailStr = "test@example.com"  # type: ignore
    # FIRST_SUPERUSER: EmailStr
    # FIRST_SUPERUSER_PASSWORD: str
    # USERS_OPEN_REGISTRATION: bool = False

    # class Config:
    #     case_sensitive = True
