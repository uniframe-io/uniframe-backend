import datetime
import os
import traceback
from typing import Any, Callable

import redis
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, JSONResponse

from server.api.router import api_router
from server.apps.user.schemas import UserDO
from server.core import dependency
from server.core.exception import EXCEPTION_LIB, NmBaseException
from server.core.middleware import (
    PrometheusMiddleware,
    RouteLoggerMiddleware,
    handle_metrics,
)
from server.core.request import parse_user_from_request
from server.libs.db.sqlalchemy import DBSessionMiddleware, engine, session_args
from server.settings import API_SETTING
from server.settings.logger import api_logger as logger
from server.utils.env_check import env_check
from server.utils.validator import validate_demo_account_route

if os.getenv("DEPLOY_ENV") == "prod":
    app = FastAPI(docs_url=None, openapi_url=None)
else:
    app = FastAPI()

if os.getenv("API_RUN_LOCATION") in ["local", "test", "minikube"]:
    env_check()

if os.getenv("API_RUN_LOCATION") in ["k8s"]:
    redis_conn = redis.Redis(
        host=API_SETTING.REDIS_DNS,
        port=6379,
        password=os.getenv("K8S_REDIS_PASSWORD"),
    )


@app.exception_handler(NmBaseException)
async def api_exception_handler(
    request: Any, exc: NmBaseException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content=exc.content_to_dict()
    )


app.add_middleware(
    DBSessionMiddleware, custom_engine=engine, session_args=session_args
)

app.add_middleware(PrometheusMiddleware, group_paths=True)
app.add_route("/metrics", handle_metrics)


@app.middleware("http")
async def check_expire(request: Request, call_next: Callable) -> Response:
    build_date = os.getenv("IMAGE_BUILD_DATE", "")
    if os.getenv("API_RUN_LOCATION") == "local" and len(build_date) > 0:
        bd = datetime.datetime.strptime(build_date, "%Y-%m-%d-%H-%M")
        now = datetime.datetime.utcnow()
        if (now - bd).days > 30:
            logger.error(f"docker image has been expired: [{bd}] [{now}]")
            raise EXCEPTION_LIB.LOCAL_DEPLOY__IMAGE_EXPIRED.value(
                "Your docker image has been expired."
            )

    response = await call_next(request)
    return response


@app.middleware("http")
async def check_demo_account_route(
    request: Request, call_next: Callable
) -> Response:
    if os.getenv("API_RUN_LOCATION") in ["k8s"]:
        demo_account_limitation = redis_conn.get("DEMO_ACCOUNT_LIMITATION")
        # N.B. the result from redis is byte type
        if demo_account_limitation == b"no":
            response = await call_next(request)
            return response
    else:
        if not API_SETTING.DEMO_ACCOUNT_LIMITATION:
            response = await call_next(request)
            return response

    if request.method.lower() == "options":
        response = await call_next(request)
        return response

    do_user = parse_user_from_request(request)
    if do_user and do_user.email == API_SETTING.DEMO_ACCOUNT_EMAIL:
        err_msg = "Demo account has no permission to do this action. Please sign up a free account to experience full functionalities of uniframe.io."
        if request.method.lower() in ["delete", "put", "patch"]:
            logger.error(
                f"Demo account has no permission to do this action: [{request.method}] [{request.url.path }]"
            )
            raise EXCEPTION_LIB.DEMO_ACCOUNT__HAS_NO_PERMISSION.value(err_msg)

        if request.method.lower() == "post" and not validate_demo_account_route(
            request.url.path
        ):
            logger.error(
                f"Demo account has no permission to do this action: [{request.method}] [{request.url.path }]"
            )
            raise EXCEPTION_LIB.DEMO_ACCOUNT__HAS_NO_PERMISSION.value(err_msg)
        if (
            request.method.lower() == "get"
            and request.url.path in API_SETTING.DEMO_ACCOUNT_GET_DISABLE_PATH
        ):
            logger.error(
                f"Demo account has no permission to do this action: [{request.method}] [{request.url.path }]"
            )
            raise EXCEPTION_LIB.DEMO_ACCOUNT__HAS_NO_PERMISSION.value(err_msg)

    response = await call_next(request)
    return response


# Fix "500 error cause a CORS error"
# https://github.com/tiangolo/fastapi/issues/775#issuecomment-592946834
@app.middleware("http")
async def catch_exceptions_middleware(
    request: Request, call_next: Any
) -> JSONResponse:
    try:
        return await call_next(request)
    except NmBaseException as exc:
        return JSONResponse(
            status_code=exc.status_code, content=exc.content_to_dict()
        )
    except Exception:
        traceback.print_exc()
        return JSONResponse(
            status_code=418,
            content="Internal server error. Please contact info@uniframe.io",
        )


app.add_middleware(
    RouteLoggerMiddleware, skip_routes=API_SETTING.ROUTER_LOOGER_SKIP_ROUTES
)

# https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
# N.B. we still keep 8080 and 8000 in the CORS list for local docker-compose deployment
origin_list = [
    f"http://{API_SETTING.COOKIE_DOMAIN}:8080",
    f"https://{API_SETTING.COOKIE_DOMAIN}:8080",
    f"http://{API_SETTING.COOKIE_DOMAIN}",
    f"https://{API_SETTING.COOKIE_DOMAIN}",
    f"http://{API_SETTING.COOKIE_DOMAIN}:8000",
    f"https://{API_SETTING.COOKIE_DOMAIN}:8000",
    f"http://api.{API_SETTING.COOKIE_DOMAIN}",
    f"https://api.{API_SETTING.COOKIE_DOMAIN}",
    f"http://doc.{API_SETTING.COOKIE_DOMAIN}",
    f"https://doc.{API_SETTING.COOKIE_DOMAIN}",
    f"http://www.{API_SETTING.COOKIE_DOMAIN}",
    f"https://www.{API_SETTING.COOKIE_DOMAIN}",
    "http://localhost:8080",
    "https://localhost:8080",
    "http://localhost",
    "https://localhost",
    "http://localhost:8000",
    "https://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# add a health check endpoint
@app.get("/health-check")
async def healthcheck() -> str:
    return "OK"


app.include_router(api_router, prefix=API_SETTING.API_V1_STR)

if os.getenv("DEPLOY_ENV") == "prod":

    @app.get("/openapi.json")
    async def get_open_api_endpoint(
        current_user: UserDO = Depends(dependency.get_current_active_user),
    ) -> JSONResponse:
        return JSONResponse(
            get_openapi(title="FastAPI", version="1", routes=app.routes)
        )

    @app.get("/docs")
    async def get_documentation(
        current_user: UserDO = Depends(dependency.get_current_active_user),
    ) -> HTMLResponse:
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")
