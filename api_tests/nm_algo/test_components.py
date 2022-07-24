import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal
from scipy.sparse.csr import csr_matrix

from server.core.exception import EXCEPTION_LIB
from server.nm_algo.post_matching import (
    JoinGTInfoTransformer,
    PostProcessingTransformer,
)
from server.nm_algo.prepare_series import ExtractNameColTransformer


@pytest.fixture
def test_df() -> pd.DataFrame:
    return pd.DataFrame(
        {"name_1": ["Amsterdam", "Utrecht"], "name_2": ["BV", "NV"]}
    )


def test_ExtractNameColTransformer(test_df: pd.DataFrame) -> None:
    result = ExtractNameColTransformer(["name_1"]).transform(test_df)
    assert_series_equal(result, test_df["name_1"])

    result = ExtractNameColTransformer(["name_1", "name_2"]).transform(test_df)
    assert_series_equal(result, pd.Series(["Amsterdam BV", "Utrecht NV"]))

    with pytest.raises(Exception) as exc_info:
        ExtractNameColTransformer([]).transform(test_df)
    assert exc_info.type == EXCEPTION_LIB.NM_ALGO__NO_NAME_COLUMN_INPUT.value

    with pytest.raises(Exception) as exc_info:
        ExtractNameColTransformer(["dummy col"]).transform(test_df)
    assert (
        exc_info.type
        == EXCEPTION_LIB.NM_ALGO__NAME_COLUMN_NOT_IN_INPUT_DATA.value
    )

    with pytest.raises(Exception) as exc_info:
        ExtractNameColTransformer("just str").transform(test_df)
    assert (
        exc_info.type
        == EXCEPTION_LIB.NM_ALGO__NAME_COLUMN_NOT_IN_INPUT_DATA.value
    )


@pytest.mark.skip(
    reason="awesome_cossim_topn has been tested in sparse-dot-topn package"
)
def test_SparseMatrixCosineSimTransformer() -> None:
    return


def test_JoinGTInfoTransformer() -> None:
    """
    Test a dummy example
    - matched sparse matrix: a 3*5 sparse matrix
    index   0       1       2       3       4
    0       0       0.85    0       0       0
    1       0       0       0       0       0
    2       0       0       0.93    0.72    0
    - gt_name_col: a series of names with length 5
    """
    name_series = pd.Series(["name0", "name1", "name2", "name3", "name4"])

    row = np.array([0, 2, 2])
    col = np.array([1, 2, 3])
    data = np.array([0.85, 0.93, 0.72])
    matched = csr_matrix((data, (row, col)), shape=(3, 5))

    result = JoinGTInfoTransformer().transform(matched, name_series)
    expected = [
        [(1, "name1", 0.85)],
        None,
        [(2, "name2", 0.93), (3, "name3", 0.72)],
    ]

    assert result == expected


def test_PostProcessingTransformer() -> None:
    # TODO: add real post processing when we implment it
    expect_mid_result = pd.DataFrame(
        {
            "nm_name": ["Zhe", "Xi", "Zimmer", "Zimmer"],
            "gt_row_no": [1, -1, 2, 3],
            "matched_name": ["name1", "N/A", "name2", "name3"],
            "score": [0.85, 0, 0.93, 0.72],
        }
    )
    matched = [
        [(1, "name1", 0.85)],
        None,
        [(2, "name2", 0.93), (3, "name3", 0.72)],
    ]
    nm_name_series = pd.Series(["Zhe", "Xi", "Zimmer"])

    gt_df_sub = pd.DataFrame(
        {
            "col1": list(range(10)),
            "col2": list(range(10, 20)),
            "col3": list(range(20, 30)),
        }
    )
    expect_final_result = pd.DataFrame(
        {
            "nm_name": ["Zhe", "Xi", "Zimmer", "Zimmer"],
            "gt_row_no": [1, -1, 2, 3],
            "matched_name": ["name1", "N/A", "name2", "name3"],
            "score": [0.85, 0, 0.93, 0.72],
            "col1": [1, "N/A", 2, 3],
            "col2": [11, "N/A", 12, 13],
            "col3": [21, "N/A", 22, 23],
        }
    )

    result = PostProcessingTransformer().transform(matched, nm_name_series)
    assert_frame_equal(result, expect_mid_result, check_names=False)

    result = PostProcessingTransformer().transform(
        matched, nm_name_series, gt_df_sub
    )

    assert_frame_equal(result, expect_final_result, check_names=False)


def test_load_df() -> None:
    # TODO: to be added
    return
