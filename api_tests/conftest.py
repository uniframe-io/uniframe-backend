import copy
import json
import os
from datetime import timedelta
from typing import Any, Callable, Dict, Generator, List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from server.api.main import app
from server.apps.dataset import schemas as dataset_schemas
from server.apps.dataset.crud import DATASET_CRUD
from server.apps.group import schemas as group_schemas
from server.apps.group.crud import GROUP_CRUD
from server.apps.media import schemas as media_schemas
from server.apps.media.crud import MEDIA_CRUD
from server.apps.nm_task import schemas as task_schemas
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.oauth import schemas as oauth_schemas
from server.apps.oauth.crud import OAUTH_CRUD
from server.apps.user import schemas as user_schemas
from server.apps.user.crud import USER_CRUD
from server.core import security
from server.libs.db.sqlalchemy import db
from server.settings import API_SETTING

DUMMY_USER_EMAIL = "dummy@uniframe.com"
DUMMY_USER_PASSWORD = "dummy123456"
SUPER_USER_EMAIL = "super@uniframe.com"
SUPER_USER_PASSWORD = "super123456"


@pytest.fixture(scope="module", autouse=True)
def get_db() -> Any:
    with db():
        yield db


@pytest.fixture(scope="session")
def db_engine() -> Callable:
    """return en pg engine"""

    def _engine(db_url: str) -> Any:
        engine = create_engine(db_url, echo=True)
        return engine

    return _engine


@pytest.fixture(scope="session", autouse=True)
def init_database(db_engine: Callable) -> Generator[None, None, None]:
    """init database"""
    db_url = API_SETTING.SQLALCHEMY_DATABASE_DEFAULT_URL
    engine = db_engine(db_url)
    conn = engine.connect()
    conn.execute("commit")
    conn.execute("create database test_nm;")
    yield
    conn.execute("commit")
    conn.execute("drop database test_nm;")
    conn.close()


@pytest.fixture(scope="module", autouse=True)
def init_table(db_engine: Callable) -> Generator[None, None, None]:
    """init table"""
    db_url = API_SETTING.SQLALCHEMY_DATABASE_PYTEST_URL

    with open("./scripts/database/postgres/init.sql") as f:
        init_sql = f.read()
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

    yield

    # delete tables
    with open("./scripts/database/postgres/delete_tables.sql") as f:
        delete_sql = f.read()
    engine = db_engine(db_url)
    conn = engine.connect()

    # connection execution_option is very important!
    # otherwise, the table may not deleted
    conn.execution_options(autocommit=True).execute(delete_sql)
    conn.close()
    engine.dispose()
    # os.system(f"cd {cwd} && alembic downgrade -1")


@pytest.fixture(scope="module", autouse=False)
def do_dummy_user(
    init_table: Any,
) -> Generator[user_schemas.UserDO, None, None]:
    """
    do_dummy_user is a fixture to generate a dummy user for unit tests
    The scope is module. So, when a pytest file finishes, do_dummy_user will be tear down
    autouse=False, so it has to be explictly declared in pytest function
    """
    do_user_create = user_schemas.UserCreateDO(
        email=DUMMY_USER_EMAIL,
        hashed_password=security.get_password_hash(DUMMY_USER_PASSWORD),
        full_name="Dummy Bear",
        login_type=user_schemas.LOGIN_TYPE.EMAIL,
    )

    do_dummy_user = USER_CRUD.create_user(do_user_create)

    yield do_dummy_user

    USER_CRUD.delete_user(do_dummy_user.id)


@pytest.fixture(scope="module", autouse=False)
def do_dummy_user_list(
    init_table: Any, request: Any
) -> Generator[List[user_schemas.UserDO], None, None]:
    """
    do_dummy_user_list is a fixture to generate a list of dummy user for unit tests
    The scope is module. So, when a pytest file finishes, do_dummy_user will be tear down
    autouse=False, so it has to be explictly declared in pytest function
    """
    nr_user_created = request.param

    dummy_user_l = []
    for idx in range(nr_user_created):
        do_user_create = user_schemas.UserCreateDO(
            email=f"dummy_{idx}@gmail.com",
            hashed_password=security.get_password_hash(DUMMY_USER_PASSWORD),
            full_name=f"Dummy Bear {idx}",
            login_type=user_schemas.LOGIN_TYPE.EMAIL,
        )
        do_dummy_user = USER_CRUD.create_user(do_user_create)
        dummy_user_l.append(do_dummy_user)

    yield dummy_user_l

    for idx in range(nr_user_created):
        USER_CRUD.delete_user(dummy_user_l[idx].id)


@pytest.fixture(scope="module", autouse=False)
def do_dummy_group(
    init_table: Any, do_dummy_user: user_schemas.UserDO
) -> Generator[group_schemas.GroupDO, None, None]:
    """
    do_dummy_group is a fixture to generate a dummy group for unit tests
    The scope is module. So, when a pytest file finishes, do_dummy_group will be tear down
    autouse=False, so it has to be explictly declared in pytest function
    """
    do_group_create = group_schemas.GroupCreateDO(
        name="Dummy Group", description="This is a dummy group for unit test"
    )
    do_dummy_group = GROUP_CRUD.create_group(do_group_create, do_dummy_user.id)

    yield do_dummy_group

    GROUP_CRUD.delete_group(do_dummy_group.id)


@pytest.fixture(scope="module", autouse=False)
def do_dummy_group_list(
    init_table: Any, do_dummy_user: user_schemas.UserDO, request: Any
) -> Generator[List[group_schemas.GroupDO], None, None]:
    """
    do_dummy_group_list is a fixture to generate a list of dummy group for unit tests
    The scope is module. So, when a pytest file finishes, do_dummy_group will be tear down
    autouse=False, so it has to be explictly declared in pytest function
    """
    nr_group_created = request.param

    dummy_group_l = []
    for idx in range(nr_group_created):
        do_group_create = group_schemas.GroupCreateDO(
            name=f"Dummy Group {idx}",
            description=f"This is a dummy group {idx} for unit test",
        )
        do_dummy_group = GROUP_CRUD.create_group(
            do_group_create, do_dummy_user.id
        )

        dummy_group_l.append(do_dummy_group)

    yield dummy_group_l

    for idx in range(nr_group_created):
        GROUP_CRUD.delete_group(dummy_group_l[idx].id)


@pytest.fixture(scope="session")
def api_client() -> Generator:
    """
    a API test client
    """
    with TestClient(app) as client:
        yield client


def get_token_header(do_user: user_schemas.UserDO) -> Dict:
    """
    generate a token by a given user
    """

    access_token_expires = timedelta(
        minutes=API_SETTING.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    a_token = security.create_access_token(
        do_user.id, expires_delta=access_token_expires
    )

    header = {"Authorization": f"Bearer {a_token}"}

    return header


@pytest.fixture(scope="module")
def dummy_user_token_header(
    do_dummy_user: user_schemas.UserDO,
) -> Generator[Dict[str, str], None, None]:
    """
    generate a token simulate the dummy user login
    """
    yield get_token_header(do_dummy_user)


@pytest.fixture(scope="module", autouse=False)
def do_super_user(
    init_table: Any,
) -> Generator[user_schemas.UserDO, None, None]:
    """
    do_dummy_user is a fixture to generate a dummy user for unit tests
    The scope is module. So, when a pytest file finishes, do_dummy_user will be tear down
    autouse=False, so it has to be explictly declared in pytest function
    """
    do_user_create = user_schemas.UserCreateDO(
        email=SUPER_USER_EMAIL,
        hashed_password=security.get_password_hash(SUPER_USER_PASSWORD),
        full_name="Super Bear",
        login_type=user_schemas.LOGIN_TYPE.EMAIL,
    )
    do_super_user = USER_CRUD.create_user(do_user_create, is_superuser=True)

    yield do_super_user

    USER_CRUD.delete_user(do_super_user.id)


@pytest.fixture(scope="module")
def super_user_token_header(
    do_super_user: user_schemas.UserDO,
) -> Generator[Dict[str, str], None, None]:
    """
    generate a token simulate the super user login
    """
    yield get_token_header(do_super_user)


@pytest.fixture()
def do_dummy_media(
    do_dummy_user: user_schemas.UserDO,
) -> Generator[media_schemas.MediaDO, None, None]:
    """
    do_dummy_media is a fixture to generate a dummy media for unit tests
    """
    do_media_create = media_schemas.MediaCreateDO(
        location="https://com-uniframe-gt-xi-test.s3.amazonaws.com/ae988c37-5e57-4f80-9368-b2c4dfb5c7f9",
        e_tag="8a9cbb395360b8d528e79b30c980e287",
        ext_info=media_schemas.MediaExtInfo(
            header=["Company Name", "Address", "Type", "Notes", "Founded Time"],
            first_n_rows="balabala",
            file_name="test_upload_file.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
        owner_id=do_dummy_user.id,
    )
    do_dummy_media = MEDIA_CRUD.create_media(do_media_create)

    yield do_dummy_media

    MEDIA_CRUD.delete_media(do_dummy_media.id)


@pytest.fixture()
def do_dummy_dataset(
    do_dummy_user: user_schemas.UserDO, do_dummy_media: media_schemas.MediaDO
) -> Generator[dataset_schemas.DatasetDO, None, None]:
    """
    do_dummy_dataset is a fixture to generate a dummy dataset for unit tests
    """
    dataset_create = dataset_schemas.DatasetCreateDO(
        name="Dummy Dataset",
        description="This is a dummy dataset for unit test by confest",
        media_id=do_dummy_media.id,
        owner_id=do_dummy_user.id,
    )

    do_dummy_dataset = DATASET_CRUD.create_dataset(dataset_create)

    yield do_dummy_dataset

    DATASET_CRUD.delete_dataset(do_dummy_dataset.id)


@pytest.fixture(scope="module", autouse=False)
def do_media_gt_small(
    do_dummy_user: user_schemas.UserDO,
) -> Generator[media_schemas.MediaDO, None, None]:
    """
    do_dataset_small is the artificial groundtruth dataset
    """
    do_media_create = media_schemas.MediaCreateDO(
        # location="s3://com-uniframe-gt-xi-test/test_data/gt-small.csv",
        location="./localfs/data/gt-small.csv",
        e_tag="6b54e4b74a9dec308cdeeae87ff624da",
        ext_info=media_schemas.MediaExtInfo(
            header=["company name", "company id"],
            first_n_rows='[{"name":"Zhe Chines Sun","seq id":1,"company id":1.0},{"name":"Zhe Chinese General","seq id":1,"company id":1.0},{"name":"Dirk Werner Nowitzki","seq id":2,"company id":2.0},{"name":"Cristiano Ronaldo","seq id":3,"company id":3.0},{"name":"Chandler Nothing found","seq id":4,"company id":null}]',
            file_name="gt-small.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
        owner_id=do_dummy_user.id,
    )
    do_dummy_media = MEDIA_CRUD.create_media(do_media_create)

    yield do_dummy_media

    MEDIA_CRUD.delete_media(do_dummy_media.id)


@pytest.fixture(scope="module", autouse=False)
def do_media_nm_small(
    do_dummy_user: user_schemas.UserDO,
) -> Generator[media_schemas.MediaDO, None, None]:
    """
    do_dataset_small is the artificial groundtruth dataset
    """
    do_media_create = media_schemas.MediaCreateDO(
        # location="s3://com-uniframe-gt-xi-test/test_data/nm-small.csv",
        location="./localfs/data/nm-small.csv",
        e_tag="2e8f41d3431e61f18fd879c97a1c8446",
        ext_info=media_schemas.MediaExtInfo(
            header=["name", "seq id", "company id"],
            first_n_rows='[{"name":"Zhe Chines Sun","seq id":1,"company id":1.0},{"name":"Zhe Chinese General","seq id":1,"company id":1.0},{"name":"Dirk Werner Nowitzki","seq id":2,"company id":2.0},{"name":"Cristiano Ronaldo","seq id":3,"company id":3.0},{"name":"Chandler Nothing found","seq id":4,"company id":null}]',
            file_name="nm-small.csv",
            media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
        ),
        owner_id=do_dummy_user.id,
    )
    do_dummy_media = MEDIA_CRUD.create_media(do_media_create)

    yield do_dummy_media

    MEDIA_CRUD.delete_media(do_dummy_media.id)


@pytest.fixture(scope="module", autouse=False)
def do_dataset_gt_small(
    do_dummy_user: user_schemas.UserDO, do_media_gt_small: media_schemas.MediaDO
) -> Generator[dataset_schemas.DatasetDO, None, None]:
    """
    do_dataset_small is the artificial groundtruth dataset
    """
    do_dataset_create = dataset_schemas.DatasetCreateDO(
        name="small dataset gt",
        description="blabla",
        owner_id=do_dummy_user.id,
        media_id=do_media_gt_small.id,
    )

    do_dummy_dataset = DATASET_CRUD.create_dataset(do_dataset_create)

    yield do_dummy_dataset

    DATASET_CRUD.delete_dataset(do_dummy_dataset.id)


@pytest.fixture(scope="module", autouse=False)
def do_dataset_nm_small(
    do_dummy_user: user_schemas.UserDO, do_media_nm_small: media_schemas.MediaDO
) -> Generator[dataset_schemas.DatasetDO, None, None]:
    """
    do_dataset_small is the artificial groundtruth dataset
    """
    do_dataset_create = dataset_schemas.DatasetCreateDO(
        name="small dataset nm",
        description="blabla",
        owner_id=do_dummy_user.id,
        media_id=do_media_nm_small.id,
    )

    do_dummy_dataset = DATASET_CRUD.create_dataset(do_dataset_create)

    yield do_dummy_dataset

    DATASET_CRUD.delete_dataset(do_dummy_dataset.id)


@pytest.fixture(scope="module", autouse=False)
def do_nm_task_cfg_dict(
    do_dataset_gt_small: dataset_schemas.DatasetDO,
) -> Generator[dict, None, None]:
    """
    build a name matching batch task by using small test data
    """
    ext_info_dict = {
        "nm_status": "init",
        "gt_dataset_config": {
            "dataset_id": do_dataset_gt_small.id,
            "search_key": "company name",
        },
        "computation_resource": {
            "computation_type": "multi-thread",
            "computation_config": {"resource_tshirt_size": "Small"},
        },
        "running_parameter": {"TTL_enable": True, "TTL": "P0DT0H30M0S"},
        "search_option": {
            "top_n": 2,
            "threshold": 0.01,
            "selected_cols": [],
        },
        "algorithm_option": {
            "type": "VECTOR_BASED",
            "value": {
                "preprocessing_option": {
                    "case_sensitive": False,
                    "company_legal_form_processing": True,
                    "initial_abbr_processing": False,
                    "punctuation_removal": True,
                    "accented_char_normalize": False,
                    "shorthands_format_processing": False,
                },
                "tokenizer_option": "WORD",
                "cos_match_type": "EXACT",
                "postprocessing_option": {"placeholder": "placeholder"},
            },
        },
        "abcxyz_privacy": {
            "data_retention_time": "P30DT0H0M0S",
            "log_retention_time": "P30DT0H0M0S",
        },
        "abcxyz_security": {"encryption": "sse-s3"},
    }

    yield ext_info_dict


@pytest.fixture(scope="module", autouse=False)
def do_nm_rt_task_cfg_dict(
    do_nm_task_cfg_dict: dict,
) -> Generator[dict, None, None]:
    rt_ext_info_dict = copy.deepcopy(do_nm_task_cfg_dict)
    yield rt_ext_info_dict


@pytest.fixture(scope="module", autouse=False)
def do_nm_batch_task_cfg_dict(
    do_nm_task_cfg_dict: dict,
    do_dataset_nm_small: dataset_schemas.DatasetDO,
) -> Generator[dict, None, None]:
    batch_ext_info_dict = copy.deepcopy(do_nm_task_cfg_dict)
    batch_ext_info_dict["nm_dataset_config"] = {
        "dataset_id": do_dataset_nm_small.id,
        "search_key": "name",
    }
    batch_ext_info_dict["running_parameter"]["TTL"] = "P0DT0H15M0S"
    yield batch_ext_info_dict


@pytest.fixture(scope="module", autouse=False)
def do_nm_batch_task_small_set(
    do_dummy_user: user_schemas.UserDO, do_nm_batch_task_cfg_dict: dict
) -> Generator[task_schemas.NmTaskDO, None, None]:
    """
    build a name matching batch task by using small test data
    """
    ext_info = task_schemas.NmCfgBatchSchema(**do_nm_batch_task_cfg_dict)

    do_task_create = task_schemas.NmTaskCreateDO(
        name="dummy-batch-task-small-set",
        description="This is a dummy task",
        is_public=False,
        type=task_schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH,
        ext_info=ext_info,
    )

    do_dummy_task = NM_TASK_CRUD.create_task(do_task_create, do_dummy_user.id)

    yield do_dummy_task

    NM_TASK_CRUD.delete_task(do_dummy_task.id)


@pytest.fixture(scope="module", autouse=False)
def do_nm_rt_task_small_set(
    do_dummy_user: user_schemas.UserDO, do_nm_rt_task_cfg_dict: dict
) -> Generator[task_schemas.NmTaskDO, None, None]:
    """
    build a name matching real-time task by using small test data
    """
    ext_info = task_schemas.NmCfgRtSchema(**do_nm_rt_task_cfg_dict)

    do_task_create = task_schemas.NmTaskCreateDO(
        name="dummy-rt-task-small-set",
        description="This is a dummy task",
        is_public=False,
        type=task_schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        ext_info=ext_info,
    )

    do_dummy_task = NM_TASK_CRUD.create_task(do_task_create, do_dummy_user.id)

    yield do_dummy_task

    NM_TASK_CRUD.delete_task(do_dummy_task.id)


@pytest.fixture(scope="module", autouse=False)
def do_dummy_dataset_list(
    init_table: Any, do_dummy_user: user_schemas.UserDO, request: Any
) -> Generator[List[dataset_schemas.DatasetDO], None, None]:
    """
    do_dummy_dataset_list is a fixture to generate a list of dummy dataset for unit tests
    """
    nr_dataset_created = request.param

    dummy_dataset_l = []
    dummy_media_l = []
    for idx in range(nr_dataset_created):
        do_media_create = media_schemas.MediaCreateDO(
            location=f"https://com-uniframe-gt-xi-test.s3.amazonaws.com/{idx}",
            e_tag=f"8a9cbb395360b8d528e79b30c980e287{idx}",
            ext_info=media_schemas.MediaExtInfo(
                header=[
                    "Company Name",
                    "Address",
                    "Type",
                    "Notes",
                    "Founded Time",
                ],
                first_n_rows="balabala",
                file_name="test_upload_file.csv",
                media_type=media_schemas.MEDIA_CONTENT_TYPE.CSV,
            ),
            owner_id=do_dummy_user.id,
        )
        do_dummy_media = MEDIA_CRUD.create_media(do_media_create)

        do_dataset_create = dataset_schemas.DatasetCreateDO(
            name=f"Dummy Dataset {idx}",
            description=f"This is a dummy dataset {idx} for unit test",
            owner_id=do_dummy_user.id,
            media_id=do_dummy_media.id,
        )
        do_dummy_group = DATASET_CRUD.create_dataset(do_dataset_create)

        dummy_media_l.append(do_dummy_media)
        dummy_dataset_l.append(do_dummy_group)

    yield dummy_dataset_l

    for idx in range(nr_dataset_created):
        DATASET_CRUD.delete_dataset(dummy_dataset_l[idx].id)
        MEDIA_CRUD.delete_media(dummy_media_l[idx].id)


@pytest.fixture(scope="module", autouse=False)
def do_dummy_oauth2_user(
    init_table: Any,
) -> Generator[user_schemas.UserDO, None, None]:
    """
    do_dummy_oauth2_user is a fixture to generate a dummy oauth2 user for unit tests
    """

    github_user_info = {
        "login": "DummyUser",
        "id": 88888888,
        "node_id": "XXXXXXXXXXXXXXXXXX",
        "avatar_url": "https://avatars.githubusercontent.com/u/88888888?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/DummyUser",
        "html_url": "https://github.com/DummyUser",
        "followers_url": "https://api.github.com/users/DummyUser/followers",
        "following_url": "https://api.github.com/users/DummyUser/following{/other_user}",
        "gists_url": "https://api.github.com/users/DummyUser/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/DummyUser/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/DummyUser/subscriptions",
        "organizations_url": "https://api.github.com/users/DummyUser/orgs",
        "repos_url": "https://api.github.com/users/DummyUser/repos",
        "events_url": "https://api.github.com/users/DummyUser/events{/privacy}",
        "received_events_url": "https://api.github.com/users/DummyUser/received_events",
        "type": "User",
        "site_admin": False,
        "name": "",
        "company": "",
        "blog": "",
        "location": "",
        "email": "",
        "hireable": "",
        "bio": "",
        "twitter_username": "",
        "public_repos": 5,
        "public_gists": 0,
        "followers": 31,
        "following": 50,
        "created_at": "2015-08-21T06:24:42Z",
        "updated_at": "2021-04-09T14:17:10Z",
    }

    do_oauth2_create = oauth_schemas.OAuth2UserCreateDO(
        full_name="dummy_oauth2_user",
        email="dummy_oauth2_user@gmail.com",
        login_type=user_schemas.LOGIN_TYPE.OAUTH2_GITHUB,
        provider=oauth_schemas.OAUTH2_PROVIDER_TYPE.PROVIDER_GITHUB,
        provider_id=88888888,
        ext_info=json.dumps(github_user_info),
    )
    do_dummy_oauth2 = OAUTH_CRUD.create_oauth2_user(do_oauth2_create)
    do_oauth2_user = USER_CRUD.get_user(do_dummy_oauth2.owner_id)
    if do_oauth2_user is None:
        return

    yield do_oauth2_user

    OAUTH_CRUD.delete_oauth2_user(do_dummy_oauth2.id)
    USER_CRUD.delete_user(do_dummy_oauth2.owner_id)


@pytest.fixture(scope="module")
def dummy_oauth2_user_token_header(
    do_dummy_oauth2_user: user_schemas.UserDO,
) -> Generator[Dict[str, str], None, None]:
    """
    generate a token simulate the dummy user login
    """
    yield get_token_header(do_dummy_oauth2_user)
