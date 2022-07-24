import pytest
from pydantic.error_wrappers import ValidationError

from server.apps.nm_task.schemas import (
    AbcXyz_TYPE,
    AbcXyzBase,
    ComputationConfigK8S,
    NmCfgBatchSchema,
    NmTaskCreateDTO,
    RunningParam,
    SearchOption,
)
from server.core.exception import EXCEPTION_LIB
from server.settings import GLOBAL_LIMIT_CONFIG


def test_AbcXyzBase() -> None:
    abcxyz_type = AbcXyz_TYPE.NAME_MATCHING_REALTIME

    # 0. a sanity check, should have no exception
    _ = AbcXyzBase(
        type=abcxyz_type,
        name="1" * GLOBAL_LIMIT_CONFIG.nm_cfg.nm_task_name_min_len,
        description="dummy description",
    )

    # 1. name must has in the range configured by the limitation.yaml
    with pytest.raises(Exception) as exc_info:
        _ = AbcXyzBase(
            type=abcxyz_type,
            name="1" * (GLOBAL_LIMIT_CONFIG.nm_cfg.nm_task_name_min_len - 1),
            description="dummy description",
        )
    assert exc_info.type == ValidationError

    with pytest.raises(Exception) as exc_info:
        _ = AbcXyzBase(
            type=abcxyz_type,
            name="1" * (GLOBAL_LIMIT_CONFIG.nm_cfg.nm_task_name_max_len + 1),
            description="dummy description",
        )
    assert exc_info.type == ValidationError

    # 2. desccription limitation
    with pytest.raises(Exception) as exc_info:
        _ = AbcXyzBase(
            type=abcxyz_type,
            name="1" * (GLOBAL_LIMIT_CONFIG.nm_cfg.nm_task_name_max_len + 1),
            description="2"
            * (GLOBAL_LIMIT_CONFIG.nm_cfg.nm_task_desc_max_len + 1),
        )
    assert exc_info.type == ValidationError


def test_ComputationConfigK8S() -> None:
    # 0. a sanity check, should have no exception
    _ = ComputationConfigK8S(resource_tshirt_size="Small")
    _ = ComputationConfigK8S(resource_tshirt_size="Medium")
    _ = ComputationConfigK8S(resource_tshirt_size="Large")

    # validate the data range
    with pytest.raises(Exception) as exc_info:
        _ = ComputationConfigK8S(resource_tshirt_size="Tiny")
    assert exc_info.type == ValidationError

    with pytest.raises(Exception) as exc_info:
        _ = ComputationConfigK8S(resource_tshirt_size="X-Large")
    assert exc_info.type == ValidationError


def test_RunningParam() -> None:
    # 0. a sanity check, should have no exception
    _ = RunningParam(TTL_enable=True, TTL="P1DT0H0M0S")

    ttl_min_sec = GLOBAL_LIMIT_CONFIG.nm_cfg.running_task_min_ttl.seconds
    _ = RunningParam(TTL_enable=False, TTL=str(ttl_min_sec))

    # validate the data range
    with pytest.raises(Exception) as exc_info:

        _ = RunningParam(
            TTL_enable=True,
            TTL=str(ttl_min_sec - 1),
        )
    assert exc_info.type == EXCEPTION_LIB.NM_CFG__RUNNING_PARAM_TTL_ERROR.value


def test_SearchOption() -> None:
    # Testing of search_key and selected_cols is in models/test_nm_cfg.py

    # 0. a sanity check, should have no exception
    _ = SearchOption(
        search_key_gt="",
        top_n=GLOBAL_LIMIT_CONFIG.nm_cfg.max_matching_nr,
        threshold=0.8,
        selected_cols=[],
    )

    # N.B.!!!
    # Pydantic will do the type conversion if they can
    # https://github.com/samuelcolvin/pydantic/issues/1098
    _ = SearchOption(
        search_key_gt="", top_n=2.5, threshold=0.8, selected_cols=[]
    )

    # validate the data range
    with pytest.raises(Exception) as exc_info:
        _ = SearchOption(
            search_key_gt="",
            top_n=GLOBAL_LIMIT_CONFIG.nm_cfg.max_matching_nr + 1,
            threshold=0.8,
            selected_cols=[],
        )
    assert exc_info.type == ValidationError

    with pytest.raises(Exception) as exc_info:
        _ = SearchOption(
            search_key_gt="", top_n=0, threshold=0.8, selected_cols=[]
        )
    assert exc_info.type == ValidationError

    with pytest.raises(Exception) as exc_info:
        _ = SearchOption(
            search_key_gt="", top_n=-1, threshold=0.8, selected_cols=[]
        )
    assert exc_info.type == ValidationError

    with pytest.raises(Exception) as exc_info:
        _ = SearchOption(
            search_key_gt="",
            top_n=GLOBAL_LIMIT_CONFIG.nm_cfg.max_matching_nr,
            threshold=-0.1,
            selected_cols=[],
        )
    assert exc_info.type == ValidationError

    with pytest.raises(Exception) as exc_info:
        _ = SearchOption(
            search_key_gt="",
            top_n=GLOBAL_LIMIT_CONFIG.nm_cfg.max_matching_nr,
            threshold=0,
            selected_cols=[],
        )
    assert exc_info.type == ValidationError

    with pytest.raises(Exception) as exc_info:
        _ = SearchOption(
            search_key_gt="",
            top_n=GLOBAL_LIMIT_CONFIG.nm_cfg.max_matching_nr,
            threshold=1.01,
            selected_cols=[],
        )
    assert exc_info.type == ValidationError


def test_NmTaskCreateDTO(do_nm_batch_task_cfg_dict: dict) -> None:
    with pytest.raises(Exception) as exc_info:
        _ = NmTaskCreateDTO(
            type="NOT_SUPPORT",
            name="dummy",
            description="dummy description",
            is_public=False,
            ext_info=NmCfgBatchSchema(**do_nm_batch_task_cfg_dict),
        )
    assert exc_info.type == EXCEPTION_LIB.NM_CFG__TYPE_NOT_VALIDE.value

    with pytest.raises(Exception) as exc_info:
        _ = NmTaskCreateDTO(
            type=AbcXyz_TYPE.NAME_MATCHING_REALTIME,
            name="dummy",
            description="dummy description",
            is_public=False,
            ext_info=None,
        )
    assert exc_info.type == ValidationError
