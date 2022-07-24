from typing import Any, List, Tuple

import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.series import Series
from scipy.sparse.csr import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin


class JoinGTInfoTransformer(BaseEstimator, TransformerMixin):
    """
    Join groundtruth information back the matching result
    """

    def __init__(self) -> None:
        return

    def fit(self, X: Any, y: Any = None) -> "JoinGTInfoTransformer":
        return self

    def transform(self, matched: csr_matrix, gt_name_col: Series) -> List:
        """
        this function does the actual job.

        Input:
          - matched: a N*M sparse matrix
            N: number of rows of the name matching set
            M: number of rows of the groundtruth set

            Example: 3*5 sparse matrix
            index   0       1       2       3       4
            0       0       0.85    0       0       0
            1       0       0       0       0       0
            2       0       0       0.93    0.72    0

            For the N names need to be matched
            - row 0: find a match, row 1 in groundtruth set, similarity score 0.85
            - row 1: not find a match
            - row 2: find two matches, row 2 and row 3 in groundtruth set, similarity score 0.93 and 0.72

          - gt_name_col: the groundtruth name series

        Return: a list of list of tuple,
            - length is the number of rows on name matching set
            - the element is a list of tuple. The length is the topn matches,
              the tuple is (row_nr in groundtruth, matched name, similarity score)
            Example: reuse the example above, and if we have gt_name_series
              pd.Seres(['name0', 'name1', 'name2', 'name3', 'name4'])
              The return value is
                [
                    [(1, 'name1', 0.85)],
                    None,
                    [(2, 'name2', 0.93), (3, 'name3', 0.72)]
                ]
        """

        def get_gt_row(
            candidate_row_l: List[int], candidate_score_l: List[float]
        ) -> List[Tuple]:
            return [
                (row_id, gt_name_col.at[row_id], round(score, 4))
                for row_id, score in zip(candidate_row_l, candidate_score_l)
            ]

        return [
            get_gt_row(row.indices, row.data) if len(row.data) > 0 else None
            for row in matched
        ]


class PostProcessingTransformer(BaseEstimator, TransformerMixin):
    """
    This is a placeholder for post processing
    To be added in future when we need
    """

    def __init__(self) -> None:
        return

    def fit(self, X: Any, y: Any = None) -> "PostProcessingTransformer":
        return self

    def transform(
        self,
        matched: List,
        nm_name_series: Series,
        gt_df_sub: DataFrame = None,
    ) -> Any:
        """
        Example:
        matched = [
                    [(1, 'name1', 0.85)],
                    None,
                    [(2, 'name2', 0.93), (3, 'name3', 0.72)]
                ]
        nm_name_series = Series(["Zhe", "Xi", "Zimmer"])

        Expected result
        [
            ['Zhe', 1, 'name1', 0.85],
            ['Zhe', None, None, None],
            ['Zhe', 2, 'name2', 0.93],
            ['Zhe', 3, 'name3', 0.72],
        ]
        """

        list_with_nm_name = [
            [[nm_name, *result] for result in results]
            if results is not None
            else [[nm_name, -1, "N/A", 0.0]]
            for nm_name, results in zip(nm_name_series, matched)
        ]

        flatten = lambda t: [  # noqa: E731
            item for sublist in t for item in sublist
        ]
        list_flattened = flatten(list_with_nm_name)

        result_df = pd.DataFrame.from_records(
            list_flattened,
            columns=["nm_name", "gt_row_no", "matched_name", "score"],
        )

        if gt_df_sub is None:
            return result_df

        result_df = pd.merge(
            result_df,
            gt_df_sub,
            how="left",
            left_on="gt_row_no",
            right_index=True,
            copy=False,
        )
        result_df = result_df.fillna("N/A")

        return result_df
