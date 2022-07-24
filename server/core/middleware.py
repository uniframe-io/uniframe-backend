import os
import time
import typing
from typing import Any, Callable, ClassVar, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    multiprocess,
)
from prometheus_client.metrics import MetricWrapperBase
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match, Mount, Route
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from server.core.request import parse_user_from_request
from server.settings.logger import api_logger as logger


class RouteLoggerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        *,
        skip_routes: typing.List[str] = None,
    ):
        self._logger = logger
        self._skip_routes = skip_routes if skip_routes else []
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self._should_route_be_skipped(request):
            return await call_next(request)

        return await self._execute_request_with_logging(request, call_next)

    def _should_route_be_skipped(self, request: Request) -> bool:
        return any(
            [
                path
                for path in self._skip_routes
                if request.url.path.startswith(path)
            ]
        )

    async def _execute_request_with_logging(
        self, request: Request, call_next: Callable
    ) -> Response:
        start_time = time.perf_counter()

        response = await self._execute_request(call_next, request)

        finish_time = time.perf_counter()
        self._logger.info(
            self._generate_success_log(
                request, response, finish_time - start_time
            )
        )

        return response

    def _generate_success_log(
        self, request: Request, response: Response, execution_time: float
    ) -> str:
        user_id: int = 0
        do_user = parse_user_from_request(request)
        if do_user:
            user_id = do_user.id

        overall_status = (
            "successful" if response.status_code < 400 else "failed"
        )
        return f"Request {overall_status}, User {user_id}, {request.method} {request.url.path}, status_code={response.status_code}, duration={execution_time:0.4f}s"

    async def _execute_request(
        self, call_next: Callable, request: Request
    ) -> Response:
        try:
            response = await call_next(request)
        except Exception:
            self._logger.exception(
                f"Request failed with exception {request.url.path}, method={request.method}"
            )
            raise
        return response


def get_matching_route_path(
    scope: Dict[Any, Any], routes: List[Route], route_name: Optional[str] = None
) -> Any:
    """
    Find a matching route and return its original path string

    Will attempt to enter mounted routes and subrouters.

    Credit to https://github.com/elastic/apm-agent-python
    """
    for route in routes:
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            route_name = route.path
            child_scope = {**scope, **child_scope}
            if isinstance(route, Mount) and route.routes:
                child_route_name = get_matching_route_path(
                    child_scope, route.routes, route_name
                )
                if child_route_name is None:
                    route_name = None
                else:
                    route_name += child_route_name
            return route_name
        elif match == Match.PARTIAL and route_name is None:
            route_name = route.path


class PrometheusMiddleware:
    """Middleware that collects Prometheus metrics for each request.
    Use in conjuction with the Prometheus exporter endpoint handler.
    """

    _metrics: ClassVar[Dict[str, MetricWrapperBase]] = {}

    def __init__(
        self,
        app: ASGIApp,
        group_paths: bool = False,
        app_name: str = "starlette",
        prefix: str = "starlette",
        buckets: Optional[List[str]] = None,
        filter_unhandled_paths: bool = False,
        skip_paths: Optional[List[str]] = None,
    ):
        self.app = app
        self.group_paths = group_paths
        self.app_name = app_name
        self.prefix = prefix
        self.filter_unhandled_paths = filter_unhandled_paths
        self.kwargs = {}
        if buckets is not None:
            self.kwargs["buckets"] = buckets
        self.skip_paths = []
        if skip_paths is not None:
            self.skip_paths = skip_paths

    # Starlette initialises middleware multiple times, so store metrics on the class
    @property
    def request_count(self) -> Any:
        metric_name = f"{self.prefix}_requests_total"
        if metric_name not in PrometheusMiddleware._metrics:
            PrometheusMiddleware._metrics[metric_name] = Counter(
                metric_name,
                "Total HTTP requests",
                ("method", "path", "status_code", "app_name"),
            )
        return PrometheusMiddleware._metrics[metric_name]

    @property
    def request_time(self) -> Any:
        metric_name = f"{self.prefix}_request_duration_seconds"
        if metric_name not in PrometheusMiddleware._metrics:
            PrometheusMiddleware._metrics[metric_name] = Histogram(
                metric_name,
                "HTTP request duration, in seconds",
                ("method", "path", "status_code", "app_name"),
                **self.kwargs,
            )
        return PrometheusMiddleware._metrics[metric_name]

    @property
    def requests_in_progress(self) -> Any:
        metric_name = f"{self.prefix}_requests_in_progress"
        if metric_name not in PrometheusMiddleware._metrics:
            PrometheusMiddleware._metrics[metric_name] = Gauge(
                metric_name,
                "Total HTTP requests currently in progress",
                ("method", "app_name"),
                multiprocess_mode="livesum",
            )
        return PrometheusMiddleware._metrics[metric_name]

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] not in ["http"]:
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        method = request.method
        path = request.url.path

        if path in self.skip_paths or method.lower() in ["options"]:
            await self.app(scope, receive, send)
            return

        begin = time.perf_counter()
        end = None

        # Increment requests_in_progress gauge when request comes in
        self.requests_in_progress.labels(method, self.app_name).inc()

        # Default status code used when the application does not return a valid response
        # or an unhandled exception occurs.
        status_code = 500

        async def wrapped_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                nonlocal status_code
                status_code = message["status"]

            if message["type"] == "http.response.body":
                nonlocal end
                end = time.perf_counter()

            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            # Decrement 'requests_in_progress' gauge after response sent
            self.requests_in_progress.labels(method, self.app_name).dec()

            if self.filter_unhandled_paths or self.group_paths:
                grouped_path = self._get_router_path(scope)

                # filter_unhandled_paths removes any requests without mapped endpoint from the metrics.
                if self.filter_unhandled_paths and grouped_path is None:
                    return

                # group_paths enables returning the original router path (with url param names)
                # for example, when using this option, requests to /api/product/1 and /api/product/3
                # will both be grouped under /api/product/{product_id}. See the README for more info.
                if self.group_paths and grouped_path is not None:
                    path = grouped_path

            labels = [method, path, status_code, self.app_name]

            # if we were not able to set end when the response body was written,
            # set it now.
            if end is None:
                end = time.perf_counter()

            self.request_count.labels(*labels).inc()
            self.request_time.labels(*labels).observe(end - begin)

    @staticmethod
    def _get_router_path(scope: Scope) -> Optional[str]:
        """Returns the original router path (with url param names) for given request."""
        if not (scope.get("endpoint", None) and scope.get("router", None)):
            return None

        base_scope = {
            "type": scope.get("type"),
            "path": scope.get("root_path", "") + scope.get("path"),
            "path_params": scope.get("path_params", {}),
            "method": scope.get("method"),
        }

        try:
            path = get_matching_route_path(
                base_scope, scope.get("router").routes  # type: ignore
            )
            return path
        except:  # noqa
            # unhandled path
            pass

        return None


def handle_metrics(request: Request) -> Response:
    """A handler to expose Prometheus metrics
    Example usage:
        ```
        app.add_middleware(PrometheusMiddleware)
        app.add_route("/metrics", handle_metrics)
        ```
    """
    registry = REGISTRY
    if (
        "prometheus_multiproc_dir" in os.environ
        or "PROMETHEUS_MULTIPROC_DIR" in os.environ
    ):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

    headers = {"Content-Type": CONTENT_TYPE_LATEST}
    return Response(generate_latest(registry), status_code=200, headers=headers)
