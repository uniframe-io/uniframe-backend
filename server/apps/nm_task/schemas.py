import enum
from collections import Hashable
from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, validator
from pydantic.datetime_parse import parse_duration
from pydantic.fields import Field

from server.apps.media.schemas import MediaExtInfo
from server.core.exception import EXCEPTION_LIB
from server.settings import GLOBAL_LIMIT_CONFIG

# from server.apps.config.schemas import RESOURCE_TSHIRT_SIZE

# -------- Base task -------------


class HashableBaseModel(BaseModel):
    def __hash__(self) -> int:
        return hash(
            (id(self),)
            + tuple(
                (
                    v if isinstance(v, Hashable) else tuple(v)
                    for v in self.__dict__.values()
                )
            )
        )


class AbcXyz_TYPE(str, enum.Enum):
    """
    all avaiable type for AbcXyz

    Currently, we support type:
    - **NAME_MATCHING_REALTIME = "NAME_MATCHING_REALTIME"**: real-time nm task. input a query record or records Q, for each record,
    find the most similar N records from a dataset B and return the result in real-time (< 10s?)
        * In the real-time query nm, dataset B  is the groundtruth dataset
        * N >=1, normally is less than 3 or 5default
    - **NAME_MATCHING_BATCH = "NAME_MATCHING_BATCH"**: batch nm task. input a dataset A, for each record, find the most similar N records from dataset B,
      and return the result in a relative long computation time.
    """

    NAME_MATCHING_BATCH = "NAME_MATCHING_BATCH"
    NAME_MATCHING_REALTIME = "NAME_MATCHING_REALTIME"


class AbcXyzPrivacy(HashableBaseModel):
    """data privacy configufation

    :field data_retention_time: timedelta that the uploaded data stays on the server side
    :field log_retention_time: timedelta that the log stays on the server side
    """

    data_retention_time: str
    log_retention_time: str

    @validator("data_retention_time")
    def data_retention_time_validation(cls, v: str, values, **kwargs) -> str:  # type: ignore
        try:
            _ = parse_duration(v)
        except Exception:
            raise EXCEPTION_LIB.NM_CFG__TIMEDELTA_PARSE_ERR.value(
                f"data_retention_time value [{v}] can be parsed as a timedelta"
            )

        return v

    @validator("log_retention_time")
    def log_retention_time_validation(cls, v: str, values, **kwargs) -> str:  # type: ignore
        try:
            _ = parse_duration(v)
        except Exception:
            raise EXCEPTION_LIB.NM_CFG__TIMEDELTA_PARSE_ERR.value(
                f"log_retention_time value [{v}] can be parsed as a timedelta"
            )

        return v


class DATA_ENCRYPTION(str, enum.Enum):
    SSE_S3 = "sse-s3"
    SSE_KMS = "sse-kms"


class AbcXyzSecurity(HashableBaseModel):
    """ecurity configuration
    - **encryption**: data encryption options, e.g., AWS S3-SSE.
    """

    encryption: DATA_ENCRYPTION


class AbcXyzBase(HashableBaseModel):
    """AbcXyz basic info
    - **nm_name**: name matching task name
    - **nm_desc**: name matching task description, max 200 characters
    """

    name: str = Field(
        min_length=GLOBAL_LIMIT_CONFIG.nm_cfg.nm_task_name_min_len,
        max_length=GLOBAL_LIMIT_CONFIG.nm_cfg.nm_task_name_max_len,
    )
    description: str = Field(
        max_length=GLOBAL_LIMIT_CONFIG.nm_cfg.nm_task_desc_max_len
    )
    is_public: bool = False
    type: AbcXyz_TYPE


class AbcXyzCreateDTOBase(AbcXyzBase):
    pass


class AbcXyzDTOBase(AbcXyzBase):
    """Name matching task basic information

    - **user_id**: user id who create this name matching task
    - **nm_id**: name matching task id
    - **nm_status** name matching task status
    """

    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class AbcXyzDOBase(AbcXyzDTOBase):
    pass


# -------- Name Matching task -------------


class NM_STATUS(str, enum.Enum):
    """Name matching task status

    Task status transistion diagram in `docs/nm-task-status-transition.drawio`
    """

    INIT = "init"  # task created but not "start" yet
    PREPARING = (
        "preparing"  # preparing the computation resource, not really start yet
    )
    LAUNCHING = "launching"  # batch task running, or real-time task preparing
    READY = (
        "ready"  # dedicated for real-time task, ready for real-time searching
    )
    TERMINATING = "terminating"  # terminating the task
    TERMINATED = "terminated"  # terminated by TTL
    FAILED = "failed"  # failed by nm task raise exception
    STOPPED = "stopped"  # stopped by user action
    OOMKILLED = "out-of-memory"  # Killed by OOM
    COMPLETE = "complete"  # task finished successfully


class POD_STATUS(str, enum.Enum):
    """Name matching K8S Pod status"""

    RUNNING = "Running"
    COMPLETED = "Completed"
    OOMKILLED = "OOMKilled"
    DELETED = "Deleted"


class NM_COMP_TYPE(str, enum.Enum):
    MULTI_THREAD = "multi-thread"
    SPARK = "spark"


class LANG_SUPPORT(enum.Enum):
    EN = "en"
    NL = "nl"


class RESOURCE_TSHIRT_SIZE(str, enum.Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


class ComputationConfigK8S(HashableBaseModel):
    """Kubernetes Computation reource configuration
    :fileld nr_cpn: number of vcpn
    :filed memory_size: memory size, unit is GiB, e.g., 16
    """

    resource_tshirt_size: RESOURCE_TSHIRT_SIZE


class ComputationResource(HashableBaseModel):
    """Computatio resource configuration
    :field computation_type: select the computation type. The supporting type is defined in `NM_COMP_TYPE`
    :field computation_config: detailed setup
    """

    computation_type: NM_COMP_TYPE
    computation_config: ComputationConfigK8S


class RunningParam(HashableBaseModel):
    """Name matching task running parameter
    :field TTL: the TTL of the running task
    """

    TTL_enable: bool = True
    TTL: str  # timedelta cannot be JSON serialized when requests.post/get

    @validator("TTL")
    def TTL_validation(cls, v: str, values, **kwargs) -> str:  # type: ignore
        if values["TTL_enable"]:
            try:
                timedelta_v = parse_duration(v)
            except Exception:
                raise EXCEPTION_LIB.NM_CFG__TIMEDELTA_PARSE_ERR.value(
                    f"TTL value [{v}] can be parsed as a timedelta"
                )
            if timedelta_v >= GLOBAL_LIMIT_CONFIG.nm_cfg.running_task_min_ttl:
                return v

            raise EXCEPTION_LIB.NM_CFG__RUNNING_PARAM_TTL_ERROR.value(
                f"The minimal value of TTL is {GLOBAL_LIMIT_CONFIG.nm_cfg.running_task_min_ttl}"
            )
        else:
            return v


class SearchOption(HashableBaseModel):
    """Name matching task searching options
    :field search_key: the search key of the groundtruth data
    :field top_n: the top-n result from a list of all matching results
    :field threshold: threshold to decide if it is a match
    :field selected_cols: when return matching result, only the selected columns will be returned
    """

    top_n: int = Field(gt=0, le=GLOBAL_LIMIT_CONFIG.nm_cfg.max_matching_nr)
    threshold: float = Field(gt=0, lt=1)
    selected_cols: List[str]


class PreprocessingOption(HashableBaseModel):
    """Name matching algorithm options.

    :field case_sensitive: case sensitive or not
    :field company_legal_form_processing: Map all the legal form abbreviations to the same format (B. V.= B.V. = B V = BV)
    :field initial_abbr_processing: Map all the abbreviations to the same format (Z. S. = Z.S. = ZS)
    :field punctuation_removal: Replace all punctuation characters with space or not
    :field accented_char_normalize: Replace accented characters by their normalized representation, e.g. replace 'ä' with 'A\xa4'
    :field shorthands_format_processing: Map all the shorthands to the same format (stichting => stg), language based
    """

    case_sensitive: bool
    company_legal_form_processing: bool
    initial_abbr_processing: bool
    punctuation_removal: bool
    accented_char_normalize: bool
    shorthands_format_processing: bool


class TokenizerType(str, enum.Enum):
    WORD = "WORD"
    SUBWORDE = "SUBWORD"


class CosineMatchingType(str, enum.Enum):
    EXACT = "EXACT"
    APPROXIMATE = "APPROXIMATE"


class CosineMatchingOption(HashableBaseModel):
    cos_match_type: CosineMatchingType


class PostProcessingOption(BaseModel):
    placeholder: Optional[str]


class AlgorithmOptionEditDistance(HashableBaseModel):
    preprocessing_option: PreprocessingOption
    postprocessing_option: PostProcessingOption


class AlgorithmOptionVectorBased(HashableBaseModel):
    preprocessing_option: PreprocessingOption
    tokenizer_option: TokenizerType
    cos_match_type: CosineMatchingType
    postprocessing_option: PostProcessingOption


class AlgorithmOptionType(str, enum.Enum):
    EDIT_DISTANCE = "EDIT_DISTANCE"
    VECTOR_BASED = "VECTOR_BASED"


class AlgorithmOption(HashableBaseModel):
    type: AlgorithmOptionType
    value: Union[AlgorithmOptionVectorBased, AlgorithmOptionEditDistance]

    @validator("value")
    def validate_value(cls, v, values, **kwargs):  # type: ignore
        if values["type"] == AlgorithmOptionType.EDIT_DISTANCE:
            return AlgorithmOptionEditDistance(**(v.dict()))

        if values["type"] == AlgorithmOptionType.VECTOR_BASED:
            return AlgorithmOptionVectorBased(**(v.dict()))


# TODO: add DO and DTO, so that DTO does not contain MatchingResult field
class BatchMatchingResult(HashableBaseModel):
    location: str
    ext_info: MediaExtInfo


class dataset_config(HashableBaseModel):
    dataset_id: int
    # select multiple column as search column?
    search_key: str


class NmCfgBatchSchema(HashableBaseModel):
    nm_status: NM_STATUS
    gt_dataset_config: dataset_config
    nm_dataset_config: dataset_config
    computation_resource: ComputationResource
    running_parameter: RunningParam
    search_option: SearchOption
    algorithm_option: AlgorithmOption
    matching_result: Optional[BatchMatchingResult]
    abcxyz_privacy: AbcXyzPrivacy
    abcxyz_security: AbcXyzSecurity


class NmCfgRtSchema(HashableBaseModel):
    nm_status: NM_STATUS
    gt_dataset_config: dataset_config
    computation_resource: ComputationResource
    running_parameter: RunningParam
    search_option: SearchOption
    algorithm_option: AlgorithmOption
    abcxyz_privacy: AbcXyzPrivacy
    abcxyz_security: AbcXyzSecurity


# N.B.: how to get the a list RUNNING real-time NM tasks which use dataset {dataset_id}
# ### Get a list RUNNING real-time NM tasks which use dataset {dataset_id}
# ``` python
# @router.get(
#     "/nm-tasks/real-time/active-dataset/{dataset_id}",
#     summary="Get a list of real-time NM tasks which use dataset {dataset_id}",
#     response_description="A list of real-time nm tasks",
# )
# ```


class NmTaskCreateDTO(AbcXyzCreateDTOBase):
    ext_info: Union[NmCfgBatchSchema, NmCfgRtSchema]

    @validator("ext_info")
    def validate_value(cls, v, values, **kwargs):  # type: ignore
        if values.get("type") is None:
            raise EXCEPTION_LIB.NM_CFG__TYPE_NOT_VALIDE.value(
                "Task type is None, not valid!"
            )

        task_type = values["type"]
        if task_type == AbcXyz_TYPE.NAME_MATCHING_BATCH:
            return NmCfgBatchSchema(**(v.dict()))

        if task_type == AbcXyz_TYPE.NAME_MATCHING_REALTIME:
            return NmCfgRtSchema(**(v.dict()))

        raise EXCEPTION_LIB.NM_CFG__TYPE_NOT_VALIDE.value(
            f"Task type is {task_type}, not valid!"
        )


class NmTaskCreateDO(NmTaskCreateDTO):
    pass


class NmTaskDO(AbcXyzDOBase):
    ext_info: Union[NmCfgBatchSchema, NmCfgRtSchema]

    @validator("ext_info")
    def validate_value(cls, v, values, **kwargs):  # type: ignore
        if values["type"] == AbcXyz_TYPE.NAME_MATCHING_BATCH:
            return NmCfgBatchSchema(**(v.dict()))

        if values["type"] == AbcXyz_TYPE.NAME_MATCHING_REALTIME:
            return NmCfgRtSchema(**(v.dict()))


class NmTaskDTO(AbcXyzDTOBase):
    ext_info: Union[NmCfgBatchSchema, NmCfgRtSchema]

    @validator("ext_info")
    def validate_value(cls, v, values, **kwargs):  # type: ignore
        if values["type"] == AbcXyz_TYPE.NAME_MATCHING_BATCH:
            return NmCfgBatchSchema(**(v.dict()))

        if values["type"] == AbcXyz_TYPE.NAME_MATCHING_REALTIME:
            return NmCfgRtSchema(**(v.dict()))


# class MatchResult(BaseModel):
#     """Matched result

#     :field matched_str: matched name, from base class
#     :row_id: the row id of the groundtruth dataset
#     :matched_row: the matched row from groundtruth dataset. It is noted it returns a subset of the row based on the configuration of nm_conifg['search_option']['selcted_cols']
#     """

#     matched_str: str
#     row_id: int
#     similarity_score: float
#     # matched_row: Optional[List[Dict[str, Any]]] = None


# class RTQueryResp(BaseModel):
#     """The nm result of a query key

#     :field query_key: the query string
#     :field match_lst: a list of nm matching results. The length of match_list should be `top_n` in search_option
#     """

#     query_key: str
#     match_list: List[Optional[MatchResult]]


class RTQueryRequst(BaseModel):
    """
    The request body of a real-time nm query
    :field query_keys: a list of search key
    :field search_option: the nm search options. It is from nm_config binded of this real-time query task
    """

    query_keys: List[str]
    search_option: SearchOption


class RTQueryResp(BaseModel):
    """The response body of a real-time nm query

    :field query_result: a list of `RTQueryResp`
    :field search_option: the nm search options. It is from nm_config binded of this real-time query task
    """

    query_result: List
    columns: List[str]
    search_option: SearchOption


class RTQueryRequestForRapidAPI(BaseModel):
    """
    The request body of a real-time nm query
    :field query_keys: a list of search key
    """

    query_keys: List[str]
