import os
import time
from typing import Any

from sqlalchemy import create_engine

from server.libs.db.sqlalchemy import db
from server.settings import API_SETTING
from server.settings.logger import test_logger as logger

logger.info(f"API_RUN_LOCATION [{os.getenv('API_RUN_LOCATION')}]")

if os.getenv("API_RUN_LOCATION") == "test":
    PG_DB_NAME = "test_nm"
else:
    PG_DB_NAME = "nm"


def get_db() -> Any:
    with db():
        yield db


def db_engine(db_url: str) -> Any:
    engine = create_engine(db_url, echo=False)
    return engine


def before_feature(context: Any, feature: Any) -> None:
    """
    Setup behave testing environment
    N.B. please don't change the code here!!! otherwise, the testing may not work!!!
    """
    db_url = API_SETTING.SQLALCHEMY_DATABASE_DEFAULT_URL
    engine = db_engine(db_url)
    conn = engine.connect()
    conn.execute("commit")
    conn.execute(f"create database {PG_DB_NAME};")
    conn.close()


def after_feature(context: Any, feature: Any) -> None:
    """
    Destroy behave testing environment
    N.B. please don't change the code here!!! otherwise, the testing may not work!!!
    """

    # destroy database
    engine = db_engine(API_SETTING.SQLALCHEMY_DATABASE_DEFAULT_URL)
    conn = engine.connect()
    conn.execute("commit")
    conn.execute(f"drop database {PG_DB_NAME};")
    conn.close()


def before_scenario(context: Any, feature: Any) -> None:
    """init table"""
    db_url = API_SETTING.SQLALCHEMY_DATABASE_PYTEST_URL
    with open("./scripts/database/postgres/init.sql") as f:
        init_sql = f.read()

    # change to table initialization from init_table to alembic
    # with open("./scripts/database/postgres/init_table.sql") as f:
    #     init_table_sql = f.read()

    init_sql = init_sql.replace("%", "%%")
    engine = db_engine(db_url)
    conn = engine.connect()
    conn.execute(init_sql)
    # conn.execute(init_table_sql)
    conn.close()
    engine.dispose()

    cwd = os.getcwd()
    os.system(f"cd {cwd} && alembic upgrade head")

    # make db context available
    get_db()

    # init context
    context.dataset_dict = {}
    context.nm_task_dict = {}

    pass


def after_scenario(context: Any, feature: Any) -> None:
    # wait for integration test DB operation stable
    time.sleep(1)

    # destroy tables
    with open("./scripts/database/postgres/delete_tables.sql") as f:
        delete_sql = f.read()

    logger.info("deconstruct integration context: delete tables")

    engine = db_engine(API_SETTING.SQLALCHEMY_DATABASE_PYTEST_URL)
    conn = engine.connect()

    # connection execution_option is very important!
    # otherwise, the table may not deleted
    conn.execution_options(autocommit=True).execute(delete_sql)

    # we can use sentence below to print tables and database
    # inspector = inspect(engine)
    # print(f"db {engine.url.database}")
    # for table_name in inspector.get_table_names():
    #     print(f"table name: {table_name}")

    conn.close()
    engine.dispose()
