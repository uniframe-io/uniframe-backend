from server.apps.dataset import schemas as dataset_schemas
from server.apps.dataset.crud import DATASET_CRUD
from server.apps.media import schemas as media_schemas
from server.apps.media.crud import MEDIA_CRUD
from server.apps.nm_task import schemas as task_schemas
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.user import schemas as user_schemas
from server.apps.user.crud import USER_CRUD
from server.core import security

DUMMY_USER_EMAIL = "dummy@example.com"
DUMMY_USER_PASSWORD = "dummy123456"


def create_dummy_user() -> user_schemas.UserDO:
    do_user_create = user_schemas.UserCreateDO(
        email=DUMMY_USER_EMAIL,
        hashed_password=security.get_password_hash(DUMMY_USER_PASSWORD),
        full_name="Dummy Bear",
        login_type=user_schemas.LOGIN_TYPE.EMAIL,
    )

    do_dummy_user = USER_CRUD.create_user(do_user_create)

    return do_dummy_user


def delete_dummy_user(dummy_user: user_schemas.UserDO) -> None:
    USER_CRUD.delete_user(dummy_user.id)


def create_media_gt_small(
    do_dummy_user: user_schemas.UserDO,
) -> media_schemas.MediaDO:
    """
    do_dataset_small is the artificial groundtruth dataset
    """
    do_media_create = media_schemas.MediaCreateDO(
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

    return do_dummy_media


def create_media_nm_small(
    do_dummy_user: user_schemas.UserDO,
) -> media_schemas.MediaDO:
    """
    do_dataset_small is the artificial groundtruth dataset
    """
    do_media_create = media_schemas.MediaCreateDO(
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

    return do_dummy_media


def create_dataset(
    do_dummy_user: user_schemas.UserDO,
    name: str,
    do_media: media_schemas.MediaDO,
) -> dataset_schemas.DatasetDO:
    """
    do_dataset_small is the artificial groundtruth dataset
    """
    do_dataset_create = dataset_schemas.DatasetCreateDO(
        name=name,
        description="blabla",
        owner_id=do_dummy_user.id,
        media_id=do_media.id,
    )

    do_dummy_dataset = DATASET_CRUD.create_dataset(do_dataset_create)

    return do_dummy_dataset


def create_realtime_nm_task(
    do_dummy_user: user_schemas.UserDO,
    do_dataset_gt_small: dataset_schemas.DatasetDO,
) -> task_schemas.NmTaskDO:
    """
    build a name matching batch task by using small test data
    """
    ext_info_dict = {
        "nm_status": "init",
        "gt_dataset_config": {
            "dataset_id": do_dataset_gt_small.id,
            "search_key_gt": "company name",
        },
        "computation_resource": {
            "computation_type": "multi-thread",
            "computation_config": {"resource_tshirt_size": "Small"},
        },
        "running_parameter": {"TTL_enable": True, "TTL": "P1DT0H0M0S"},
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
                "tokenizer_option": "SUBWORD",
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

    ext_info = task_schemas.NmCfgRtSchema(**ext_info_dict)

    do_task_create = task_schemas.NmTaskCreateDO(
        name="dummy-realtime-task-small-set",
        description="This is a dummy task",
        is_public=False,
        type=task_schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        ext_info=ext_info,
    )

    do_dummy_task = NM_TASK_CRUD.create_task(do_task_create, do_dummy_user.id)

    return do_dummy_task


def create_batch_nm_task(
    do_dummy_user: user_schemas.UserDO,
    do_dataset_gt_small: dataset_schemas.DatasetDO,
    do_dataset_nm_small: dataset_schemas.DatasetDO,
) -> task_schemas.NmTaskDO:
    """
    build a name matching batch task by using small test data
    """
    ext_info_dict = {
        "nm_status": "init",
        "gt_dataset_config": {
            "dataset_id": do_dataset_gt_small.id,
            "search_key": "company name",
        },
        "nm_dataset_config": {
            "dataset_id": do_dataset_nm_small.id,
            "search_key": "name",
        },
        "computation_resource": {
            "computation_type": "multi-thread",
            "computation_config": {"resource_tshirt_size": "Small"},
        },
        "running_parameter": {"TTL_enable": True, "TTL": "P0DT2H0M0S"},
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
                "tokenizer_option": "SUBWORD",
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

    ext_info = task_schemas.NmCfgBatchSchema(**ext_info_dict)

    do_task_create = task_schemas.NmTaskCreateDO(
        name="dummy-batch-task-small-set",
        description="This is a dummy task",
        is_public=False,
        type=task_schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH,
        ext_info=ext_info,
    )

    do_dummy_task = NM_TASK_CRUD.create_task(do_task_create, do_dummy_user.id)

    return do_dummy_task
