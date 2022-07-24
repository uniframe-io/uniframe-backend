"""
This file define the Error class used in name matching solution
We mainly refer to this article https://www.jianshu.com/p/f3caf01187d2


"""
import enum


class NmBaseException(Exception):
    """Base class of custom exception class

    :param error_domain: custom defined error domain
    :param message: detail error message
    """

    def __init__(self, error_domain: str, message: str) -> None:
        self.error_domain = error_domain
        self.message = message
        self.status_code = 418

    def __str__(self) -> str:
        """string representation for error backtrace"""
        return (
            f"\n\t- domain:\t{self.error_domain}\n\t- message:\t{self.message}"
        )

    def content_to_dict(self) -> dict:
        """dictionary representaiton for FastAPI exception handling"""
        return {
            "error_domain": self.error_domain,
            "message": self.message,
        }


def ErrorClassFactory(
    error_domain: str, base_exception_class: type = NmBaseException
) -> type:
    """
    Create Exception class dynamically
    inspired by this https://stackoverflow.com/a/15247892
    """

    def __init__(self: NmBaseException, message: str) -> None:
        base_exception_class.__init__(  # type: ignore
            base_exception_class, error_domain=error_domain, message=message
        )

    name = f"EXCEPTION_{error_domain}"
    exception_class = type(
        name, (base_exception_class,), {"__init__": __init__}
    )

    return exception_class


class EXCEPTION_LIB(enum.Enum):
    """
    Customized Error Exception Library

    We design it as a enum type, so that mypy and Python editor python plugin (pylance if use VSCode) can have value check
    The value of enum is the dynamically generated exception class

    Name convention:
        - start with module
        -
        - detailed error
    """

    # General error, only use this when don't know which one to use
    GENERAL__ERROR = ErrorClassFactory(error_domain="GENERAL__ERROR")

    GENERAL__ENV_NOT_ASSIGNED = ErrorClassFactory(
        error_domain="GENERAL__ENV_NOT_ASSIGNED"
    )

    # ---------------------------------
    # Name matching configuration error
    NM_CFG__GENERAL_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__GENERAL_ERROR"
    )
    NM_CFG__ID_NOT_BELONG_TO_USER = ErrorClassFactory(
        error_domain="NM_CFG__ID_NOT_BELONG_TO_USER"
    )
    NM_CFG__ID_NOT_EXIST = ErrorClassFactory(
        error_domain="NM_CFG__ID_NOT_EXIST"
    )
    NM_CFG__TYPE_NOT_VALIDE = ErrorClassFactory(
        error_domain="NM_CFG__TYPE_NOT_VALIDE"
    )
    NM_CFG__STATUS_NOT_VALID = ErrorClassFactory(
        error_domain="NM_CFG__STATUS_NOT_VALID"
    )
    NM_CFG__GROUND_TRUTH_DATA_ERR = ErrorClassFactory(
        error_domain="NM_CFG__GROUND_TRUTH_DATA_ERR"
    )
    NM_CFG__GROUND_TRUTH_HEADER_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__GROUND_TRUTH_HEADER_ERROR"
    )
    NM_CFG__COMPUTATION_RESOURCE_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__COMPUTATION_RESOURCE_ERROR"
    )
    NM_CFG__RUNNING_PARAM_TTL_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__RUNNING_PARAM_TTL_ERROR"
    )
    NM_CFG__SEARCH_OPT_SERACH_KEY_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__SEARCH_OPT_SERACH_KEY_ERROR"
    )
    NM_CFG__SEARCH_OPT_TOP_N_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__SEARCH_OPT_TOP_N_ERROR"
    )
    NM_CFG__SEARCH_OPT_THRESHOLD_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__SEARCH_OPT_THRESHOLD_ERROR"
    )
    NM_CFG__SEARCH_OPT_SELECTED_COL_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__SEARCH_OPT_SELECTED_COL_ERROR"
    )
    NM_CFG__CRUD_FACTORY_NOT_FOUND = ErrorClassFactory(
        error_domain="NM_CFG__CRUD_FACTORY_NOT_FOUND"
    )
    NM_CFG__CREATE_DUMMY_TASK_ERROR = ErrorClassFactory(
        error_domain="NM_CFG__CREATE_DUMMY_TASK_ERROR"
    )
    NM_CFG__TIMEDELTA_PARSE_ERR = ErrorClassFactory(
        error_domain="NM_CFG__TTL_PARSE_ERR"
    )
    # ---------------------------------
    # IO error
    IO__DEFAULT_GLOBAL_CFG_FILE_CANNOT_OPEN = ErrorClassFactory(
        error_domain="IO__DEFAULT_GLOBAL_CFG_FILE_CANNOT_OPEN"
    )
    IO__NM_CFG_FILE_NOT_EXIST = ErrorClassFactory(
        error_domain="IO__NM_CFG_FILE_NOT_EXIST"
    )
    IO__YMAL_FILE_CANNOT_PARSE = ErrorClassFactory(
        error_domain="IO__YMAL_FILE_CANNOT_PARSE"
    )
    IO__YAML_FILE_NOT_EXIST = ErrorClassFactory(
        error_domain="IO__YAML_FILE_NOT_EXIST"
    )
    IO__JSON_FILE_CANNOT_PARSE = ErrorClassFactory(
        error_domain="IO__JSON_FILE_CANNOT_PARSE"
    )
    IO__USER_FILE_NOT_EXIST = ErrorClassFactory(
        error_domain="IO__USER_FILE_NOT_EXIST"
    )

    # -----------------------------------
    # User error
    USER__EMAIL_ALREADY_EXISTS = ErrorClassFactory(
        error_domain="USER__EMAIL_ALREADY_EXISTS"
    )
    USER__EMAIL_NOT_EXISTS = ErrorClassFactory(
        error_domain="USER__EMAIL_NOT_EXISTS"
    )
    USER__USER_ID_NOT_EXIST = ErrorClassFactory(
        error_domain="USER__USER_ID_NOT_EXIST"
    )
    USER__SUPERUSER_HAS_NO_NM_TASK = ErrorClassFactory(
        error_domain="USER__SUPERUSER_HAS_NO_NM_TASK"
    )
    USER__SUPERUSER_CANNOT_CREATE_NM_TASK = ErrorClassFactory(
        error_domain="USER__SUPERUSER_CANNOT_CREATE_NM_TASK"
    )
    USER__CANNOT_FIND_NM_TASK_RECORD_IN_DB = ErrorClassFactory(
        error_domain="USER__CANNOT_FIND_NM_TASK_RECORD_IN_DB"
    )
    USER__CREATE_FAILED = ErrorClassFactory(error_domain="USER__CREATE_FAILED")
    USER__UPDATE_FAILED = ErrorClassFactory(error_domain="USER__UPDATE_FAILED")

    USER__LOGIN_TYPE_ERROR = ErrorClassFactory(
        error_domain="USER__LOGIN_TYPE_ERROR"
    )
    USER__RESET_PASSWORD_ERROR = ErrorClassFactory(
        error_domain="USER__RESET_PASSWORD_ERROR"
    )

    # ---------------------------------
    # AWS Implementation error
    PLATFORM__AWS__S3__CLIENT_ERROR = ErrorClassFactory(
        error_domain="PLATFORM__AWS__S3__CLIENT_ERROR"
    )
    PLATFORM__AWS__S3__RESOURCE_EXISTS = ErrorClassFactory(
        error_domain="PLATFORM__AWS__S3__RESOURCE_EXISTS"
    )
    PLATFORM__AWS__S3__UPLOAD_FILE_ERROR = ErrorClassFactory(
        error_domain="PLATFORM__AWS__S3__UPLOAD_FILE_ERROR"
    )
    PLATFORM__AWS__S3__GENERATE_PRESIGN_URL_ERROR = ErrorClassFactory(
        error_domain="PLATFORM__AWS__S3__GENERATE_PRESIGN_URL_ERROR"
    )
    PLATFORM__AWS__DYNAMODB__OPERATION_ERROR = ErrorClassFactory(
        error_domain="PLATFORM__AWS__DYNAMODB__OPERATION_ERROR"
    )

    PLATFORM__LOCALFS__WRITE_ERROR = ErrorClassFactory(
        error_domain="PLATFORM__LOCALFS__ERROR"
    )
    PLATFORM__LOCALFS__READ_ERROR = ErrorClassFactory(
        error_domain="PLATFORM__LOCALFS__ERROR"
    )

    # ---------------------------------
    # NM realtime query error
    NM_RT__EXCEED_MAX_RT_NR_QUERIES_LIMIT = ErrorClassFactory(
        error_domain="NM_RT__EXCEED_MAX_RT_NR_QUERIES_LIMIT"
    )
    NM_RT__TASK_TYPE_ERR = ErrorClassFactory(
        error_domain="NM_RT__TASK_TYPE_ERR"
    )
    NM_RT__TASK_NOT_READY = ErrorClassFactory(
        error_domain="NM_RT__TASK_NOT_READY"
    )

    # ---------------------------------
    # NM batch query error

    # ---------------------------------
    # API endpoint error
    API__CURRENT_USER_NOT_IN_DB = ErrorClassFactory(
        error_domain="API__CURRENT_USER_NOT_IN_DB"
    )
    API__INVALID_AUTHORIZATOIN_SCHEMA = ErrorClassFactory(
        error_domain="API__INVALID_AUTHORIZATOIN_SCHEMA"
    )
    API__INACTIVE_USER = ErrorClassFactory(error_domain="API__INACTIVE_USER")
    API__NO_ENOUGH_PRIVILEGE = ErrorClassFactory(
        error_domain="API__NO_ENOUGH_PRIVILEGE"
    )
    API__NOT_A_REQUIED_USER_GROUP = ErrorClassFactory(
        error_domain="API__NOT_A_REQUIED_USER_GROUP"
    )
    API__VALIDATE_CRDENTIALS_ERROR = ErrorClassFactory(
        error_domain="API__VALIDATE_CRDENTIALS_ERROR"
    )

    # ----------------------------------
    # User error
    TASK__CREATE_FAILED = ErrorClassFactory(error_domain="TASK__CREATE_FAILED")
    TASK__TASK_TYPE_NOT_VALID = ErrorClassFactory(
        error_domain="TASK__TASK_TYPE_NOT_VALID"
    )
    TASK__DB_RECORD_INTEGRATY_ERR = ErrorClassFactory(
        error_domain="TASK__DB_RECORD_INTEGRATY_ERR"
    )
    TASK__TASK_OWNER_ID_NOT_IN_USER_TABLE = ErrorClassFactory(
        error_domain="TASK__TASK_OWNER_ID_NOT_IN_USER_TABLE"
    )
    TASK__TASK_TYPE_NOT_CORRECT = ErrorClassFactory(
        error_domain="TASK__TASK_TYPE_NOT_CORRECT"
    )
    TASK__CURRENT_TASK_NAME_ALREADY_EXIST = ErrorClassFactory(
        error_domain="TASK__CURRENT_TASK_NAME_ALREADY_EXIST"
    )
    TASK__CURRENT_TASK_NOT_EXIST = ErrorClassFactory(
        error_domain="TASK__CURRENT_TASK_NOT_EXIST"
    )
    TASK__WRONG_TOKENIZATION_OPTION = ErrorClassFactory(
        error_domain="TASK__WRONG_TOKENIZATION_OPTION"
    )
    TASK__CURRENT_USER_HAS_NO_PERMISSION = ErrorClassFactory(
        error_domain="TASK__CURRENT_USER_HAS_NO_PERMISSION"
    )
    Task__Task_ID_NOT_EXIST = ErrorClassFactory(
        error_domain="Task__Task_ID_NOT_EXIST"
    )
    TASK__CURRENT_TASK_NOT_ACTIVE = ErrorClassFactory(
        error_domain="TASK__CURRENT_TASK_NOT_ACTIVE"
    )
    TASK__GT_DATASET_NOT_EXIST = ErrorClassFactory(
        error_domain="TASK__GT_DATASET_NOT_EXIST"
    )
    TASK__COMP_RESOURCE_NOT_SUPPORTED = ErrorClassFactory(
        error_domain="TASK__COMP_RESOURCE_NOT_SUPPORTED"
    )
    TASK__STATUS_DISORDER = ErrorClassFactory(
        error_domain="TASK__STATUS_DISORDER"
    )
    TASK__UPDATE_FAILED = ErrorClassFactory(error_domain="TASK__UPDATE_FAILED")

    # ----------------------------------
    # Group error
    GROUP__CURRENT_USER_HAS_NO_PERMISSION = ErrorClassFactory(
        error_domain="GROUP__CURRENT_USER_HAS_NO_PERMISSION"
    )
    GROUP__CURRENT_GROUP_NOT_EXIST = ErrorClassFactory(
        error_domain="GROUP__CURRENT_GROUP_NOT_EXIST"
    )
    GROUP__CURRENT_GROUP_NOT_ACTIVE = ErrorClassFactory(
        error_domain="GROUP__CURRENT_GROUP_NOT_ACTIVE"
    )
    GROUP__CURRENT_GROUP_NAME_ALREADY_EXIST = ErrorClassFactory(
        error_domain="GROUP__CURRENT_GROUP_NAME_ALREADY_EXIST"
    )
    GROUP__GROUP_TABLE_MEMBER_TABLE_OUT_OF_SYNC = ErrorClassFactory(
        error_domain="GROUP__GROUP_TABLE_MEMBER_TABLE_OUT_OF_SYNC"
    )
    GROUP__GROUP_OWNER_ID_NOT_IN_USER_TABLE = ErrorClassFactory(
        error_domain="GROUP__GROUP_OWNER_ID_NOT_IN_USER_TABLE"
    )
    GROUP__GROUP_STILL_USED_BY_OTHER_TABLES = ErrorClassFactory(
        error_domain="GROUP__GROUP_STILL_USED_BY_OTHER_TABLES"
    )
    GROUP__GROUP_ID_NOT_EXIST = ErrorClassFactory(
        error_domain="GROUP__GROUP_ID_NOT_EXIST"
    )
    GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_INTEGRITY_ERROR = ErrorClassFactory(
        error_domain="GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_INTEGRITY_ERROR"
    )
    GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_NOT_EXIST = ErrorClassFactory(
        error_domain="GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_NOT_EXIST"
    )
    # ----------------------------------
    # Dataset error
    DATASET__CURRENT_USER_HAS_NO_PERMISSION = ErrorClassFactory(
        error_domain="DATASET__CURRENT_USER_HAS_NO_PERMISSION"
    )
    DATASET__CURRENT_DATASET_NOT_EXIST = ErrorClassFactory(
        error_domain="DATASET__CURRENT_DATASET_NOT_EXIST"
    )
    GROUP__CURRENT_DATASET_NOT_ACTIVE = ErrorClassFactory(
        error_domain="GROUP__CURRENT_DATASET_NOT_ACTIVE"
    )
    DATASET__CURRENT_DATASET_NOT_ACTIVE = ErrorClassFactory(
        error_domain="DATASET__CURRENT_DATASET_NOT_ACTIVE"
    )
    DATASET__CURRENT_DATASET_NAME_ALREADY_EXIST = ErrorClassFactory(
        error_domain="DATASET__CURRENT_DATASET_NAME_ALREADY_EXIST"
    )
    DATASET__CREATE_FAILED = ErrorClassFactory(
        error_domain="DATASET__CREATE_FAILED"
    )
    DATASET__UPDATE_FAILED = ErrorClassFactory(
        error_domain="DATASET__UPDATE_FAILED"
    )
    DATASET__DELETE_FAILED = ErrorClassFactory(
        error_domain="DATASET__DELETE_FAILED"
    )
    # ----------------------------------
    # Media error
    MEDIA__MIME_TYPE_ERROR = ErrorClassFactory(
        error_domain="MEDIA__MIME_TYPE_ERROR"
    )
    MEDIA__CURRENT_FILE_ALREADY_EXIST = ErrorClassFactory(
        error_domain="MEDIA__CURRENT_FILE_ALREADY_EXIST"
    )
    MEDIA__CREATE_FAILED = ErrorClassFactory(
        error_domain="MEDIA__CREATE_FAILED"
    )
    MEDIA__CURRENT_MEDIA_NOT_EXIST = ErrorClassFactory(
        error_domain="MEDIA__CURRENT_MEDIA_NOT_EXIST"
    )
    MEDIA__CURRENT_USER_HAS_NO_PERMISSION = ErrorClassFactory(
        error_domain="MEDIA__CURRENT_USER_HAS_NO_PERMISSION"
    )
    MEDIA__PARSE_FILE_ERROR = ErrorClassFactory(
        error_domain="MEDIA__PARSE_FILE_ERROR"
    )
    MEDIA__FILE_ETAG_CHECK_ERROR = ErrorClassFactory(
        error_domain="MEDIA__FILE_ETAG_CHECK_ERROR"
    )
    MEDIA__FILE_CONTENT_LENGTH_ERROR = ErrorClassFactory(
        error_domain="MEDIA__FILE_CONTENT_LENGTH_ERROR"
    )

    # ---------------------------------
    # NM algorithm related error
    NM_ALGO__NO_NAME_COLUMN_INPUT = ErrorClassFactory(
        error_domain="NM_ALGO__NO_NAME_COLUMN_INPUT"
    )
    NM_ALGO__NAME_COLUMN_NOT_IN_INPUT_DATA = ErrorClassFactory(
        error_domain="NM_ALGO__NAME_COLUMN_NOT_IN_INPUT_DATA"
    )
    NM_ALGO__MATCHER_INCOMPATIBLE = ErrorClassFactory(
        error_domain="NM_ALGO__MATCHER_INCOMPATIBLE"
    )
    NM_ALGO__NAME_MATCHING_TYPE_ERROR = ErrorClassFactory(
        error_domain="NM_ALGO__NAME_MATCHING_TYPE_ERROR"
    )
    NM_ALGO__PREPROCESSING_PIPELINE_NOT_INIT = ErrorClassFactory(
        error_domain="NM_ALGO__PREPROCESSING_PIPELINE_NOT_INIT"
    )

    # ---------------------------------
    # DB and Sqlachemy error
    DB__CREATE_SQLAlCHEMY_ENGINE_FAILED = ErrorClassFactory(
        error_domain="DB__CREATE_SQLAlCHEMY_ENGINE_FAILED"
    )
    DB__CRUD_SQLAlCHEMY_ERROR = ErrorClassFactory(
        error_domain="DB__CRUD_SQLAlCHEMY_ERROR"
    )
    DB__SQLALCHEMY_MISSING_SESSION_ERR = ErrorClassFactory(
        error_domain="DB__SQLALCHEMY_MISSING_SESSION_ERR"
    )
    DB__SQLALCHEMY_SESSION_NOT_INIT_ERR = ErrorClassFactory(
        error_domain="DB__SQLALCHEMY_SESSION_NOT_INIT_ERR"
    )

    # ---------------------------------
    # OAUTH2 error
    OAUTH2__GITHUB_REQUEST_ERROR = ErrorClassFactory(
        error_domain="OAUTH2__GITHUB_REQUEST_ERROR"
    )
    OAUTH2__GITHUB_REQUEST_USER_ERROR = ErrorClassFactory(
        error_domain="OAUTH2__GITHUB_REQUEST_USER_ERROR"
    )
    OAUTH2__CREATE_FAILED = ErrorClassFactory(
        error_domain="OAUTH2__CREATE_FAILED"
    )
    OAUTH2__USER_CREATE_FAILED = ErrorClassFactory(
        error_domain="OAUTH2__USER_CREATE_FAILED"
    )

    # ---------------------------------
    # AWS error
    AWS__GET_ARC4_SECRET_ERR = ErrorClassFactory(
        error_domain="AWS__GET_ARC4_SECRET_ERR"
    )

    # ---------------------------------
    # Executor related error
    EXECUTOR__NOT_IMPLEMENTED = ErrorClassFactory(
        error_domain="EXECUTOR__NOT_IMPLEMENTED"
    )
    EXECUTOR__RQ_QUEUE_NAME_INCORRECT = ErrorClassFactory(
        error_domain="EXECUTOR__RQ_QUEUE_NAME_INCORRECT"
    )
    EXECUTOR__TASK_SUBPROCESSOR_STAR_ERR = ErrorClassFactory(
        error_domain="EXECUTOR__TASK_SUBPROCESSOR_STAR_ERR"
    )
    EXECUTOR__TASK_WORKER_NOT_AVAILABLE = ErrorClassFactory(
        error_domain="EXECUTOR__TASK_WORKER_NOT_AVAILABLE"
    )
    EXECUTOR__K8S_STAR_ERR = ErrorClassFactory(
        error_domain="EXECUTOR__K8S_STAR_ERR"
    )
    EXECUTOR__POD_NAME_NOT_AVAILABLE = ErrorClassFactory(
        error_domain="EXECUTOR__POD_NAME_NOT_AVAILABLE"
    )

    # ---------------------------------
    # TASK COMPUTE related error
    TASK_COMPUTE__TASK_ID_NOT_CORRECT = ErrorClassFactory(
        error_domain="TASK_COMPUTE__TASK_ID_NOT_CORRECT"
    )
    TASK_COMPUTE__TASK_TYPE_NOT_EXPECTED = ErrorClassFactory(
        error_domain="TASK_COMPUTE__TASK_TYPE_NOT_EXPECTED"
    )
    TASK_COMPUTE__TASK_NOT_COMPLETE = ErrorClassFactory(
        error_domain="TASK_COMPUTE__TASK_NOT_COMPLETE"
    )
    TASK_COMPUTE__MAX_RUNNING_TASK_NR_REACH = ErrorClassFactory(
        error_domain="TASK_COMPUTE__MAX_RUNNING_TASK_NR_REACH"
    )
    TASK_COMPUTE__MEM_LIMIT_NOT_SET = ErrorClassFactory(
        error_domain="TASK_COMPUTE__MEM_LIMIT_NOT_SET"
    )
    TASK_COMPUTE__TASK_HAS_BEEN_RUNNING = ErrorClassFactory(
        error_domain="TASK_COMPUTE__TASK_HAS_BEEN_RUNNING"
    )
    TASK_COMPUTE__MONTHLY_RUN_QUOTA_REACH = ErrorClassFactory(
        error_domain="TASK_COMPUTE__MONTHLY_RUN_QUOTA_REACH"
    )

    # --------------------------------

    NAME_INVALID = ErrorClassFactory(error_domain="NAME_INVALID")

    # ---------------------------------
    # VERICATION CODE related error
    VCODE__EXCCEED_LIMIT = ErrorClassFactory(
        error_domain="VCODE__EXCCEED_LIMIT"
    )
    VCODE__CURRENT_VCODE_NOT_EXIST = ErrorClassFactory(
        error_domain="VCODE__CURRENT_VCODE_NOT_EXIST"
    )
    VCODE__CURRENT_VCODE_NOT_CORRECT = ErrorClassFactory(
        error_domain="VCODE__CURRENT_VCODE_NOT_CORRECT"
    )
    VCODE__CURRENT_VCODE_EXPIRED = ErrorClassFactory(
        error_domain="VCODE__CURRENT_VCODE_EXPIRED"
    )
    VCODE__ACTION_TYPE_ERROR = ErrorClassFactory(
        error_domain="VCODE__ACTION_TYPE_ERROR"
    )
    VCODE__CREATE_FAILED = ErrorClassFactory(
        error_domain="VCODE__CREATE_FAILED"
    )
    VCODE__VCODE_SEND_FAILED = ErrorClassFactory(
        error_domain="VCODE__VCODE_SEND_FAILED"
    )

    # ---------------------------------
    # KUBERNETES related error
    KUBERNETES__CONFIG_ERROR = ErrorClassFactory(
        error_domain="KUBERNETES__CONFIG_ERROR"
    )

    # ---------------------------------
    # local deploy related error
    LOCAL_DEPLOY__CREATE_FAILED = ErrorClassFactory(
        error_domain="LOCAL_DEPLOY__CREATE_FAILED"
    )
    LOCAL_DEPLOY__UPDATE_FAILED = ErrorClassFactory(
        error_domain="LOCAL_DEPLOY__UPDATE_FAILED"
    )
    LOCAL_DEPLOY__REQUEST_ALREADY_EXISTS = ErrorClassFactory(
        error_domain="LOCAL_DEPLOY__REQUEST_ALREADY_EXISTS"
    )
    LOCAL_DEPLOY__REQUEST_NOT_EXISTS = ErrorClassFactory(
        error_domain="LOCAL_DEPLOY__REQUEST_NOT_EXISTS"
    )
    LOCAL_DEPLOY__REQUEST_NOT_APPROVED = ErrorClassFactory(
        error_domain="LOCAL_DEPLOY__REQUEST_NOT_APPROVED"
    )
    LOCAL_DEPLOY__APPROVAL_EXPIRED = ErrorClassFactory(
        error_domain="LOCAL_DEPLOY__APPROVAL_EXPIRED"
    )
    LOCAL_DEPLOY__IMAGE_EXPIRED = ErrorClassFactory(
        error_domain="LOCAL_DEPLOY__IMAGE_EXPIRED"
    )

    # ---------------------------------
    # demo account permission error
    DEMO_ACCOUNT__HAS_NO_PERMISSION = ErrorClassFactory(
        error_domain="DEMO_ACCOUNT__HAS_NO_PERMISSION"
    )

    RAPIDAPI__SECRET_ERROR = ErrorClassFactory(
        error_domain="RAPIDAPI__SECRET_ERROR"
    )
