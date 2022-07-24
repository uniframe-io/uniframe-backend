import os
from contextvars import ContextVar
from typing import Any, Dict, Optional, Union

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.types import ASGIApp

from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING

Base = declarative_base()

print("sqlalchemy check: API_RUN_LOCATION", os.getenv("API_RUN_LOCATION"))

if os.getenv("API_RUN_LOCATION") == "test":
    # run pytest
    engine = create_engine(
        API_SETTING.SQLALCHEMY_DATABASE_PYTEST_URL, poolclass=NullPool
    )
elif os.environ.get("API_RUN_LOCATION") == "local":
    # local hosting
    engine = create_engine(
        API_SETTING.SQLALCHEMY_DATABASE_LOCAL_URL,
        poolclass=NullPool,
    )
elif os.environ.get("API_RUN_LOCATION") == "minikube":
    # local hosting
    engine = create_engine(
        API_SETTING.SQLALCHEMY_DATABASE_MINIKUBE_URL,
        poolclass=NullPool,
    )
else:
    # deploy on cloud environment. dev/staging/pre-prod/prod
    engine = create_engine(API_SETTING.SQLALCHEMY_DATABASE_URL)


session_args = {
    "autocommit": False,
    "autoflush": False,
    "expire_on_commit": False,
}

_Session: sessionmaker = None
_session: ContextVar[Optional[Session]] = ContextVar("_session", default=None)


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        db_url: Optional[Union[str, URL]] = None,
        custom_engine: Optional[Engine] = None,
        engine_args: Dict = None,
        session_args: Dict = None,
        commit_on_exit: bool = False,
    ):
        super().__init__(app)
        global _Session
        engine_args = engine_args or {}
        self.commit_on_exit = commit_on_exit

        session_args = session_args or {}
        if not custom_engine and not db_url:
            raise ValueError(
                "You need to pass a db_url or a custom_engine parameter."
            )
        if not custom_engine:
            engine = create_engine(db_url, **engine_args)
        else:
            engine = custom_engine
        _Session = sessionmaker(bind=engine, **session_args)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Any:
        with db(commit_on_exit=self.commit_on_exit):
            response = await call_next(request)
        return response


class DBSessionMeta(type):
    # using this metaclass means that we can access db.session as a property at a class level,
    # rather than db().session
    @property
    def session(self) -> Session:
        """Return an instance of Session local to the current async context."""
        if _Session is None:
            raise EXCEPTION_LIB.DB__SQLALCHEMY_SESSION_NOT_INIT_ERR.value(
                """
        Session not initialised! Ensure that DBSessionMiddleware has been initialised before
        attempting database access.
        """
            )

        session = _session.get()
        if session is None:
            raise EXCEPTION_LIB.DB__SQLALCHEMY_MISSING_SESSION_ERR.value(
                """
        No session found! Either you are not currently in a request context,
        or you need to manually create a session context by using a `db` instance as
        a context manager e.g.:
        with db():
            db.session.query(User).all()
        """
            )

        return session


class DBSession(metaclass=DBSessionMeta):
    def __init__(self, session_args: Dict = None, commit_on_exit: bool = False):
        self.token = None
        self.session_args = session_args or {}
        self.commit_on_exit = commit_on_exit

    def __enter__(self) -> Any:
        if not isinstance(_Session, sessionmaker):
            raise EXCEPTION_LIB.DB__SQLALCHEMY_SESSION_NOT_INIT_ERR.value(
                """
        Session not initialised! Ensure that DBSessionMiddleware has been initialised before
        attempting database access.
        """
            )
        self.token = _session.set(_Session(**self.session_args))  # type: ignore
        return type(self)

    def __exit__(self, exc_type, exc_value, traceback) -> Any:  # type: ignore
        sess = _session.get()
        if exc_type is not None:
            sess.rollback()  # type: ignore

        if self.commit_on_exit:
            sess.commit()  # type: ignore

        sess.close()  # type: ignore
        _session.reset(self.token)  # type: ignore


db: DBSessionMeta = DBSession
