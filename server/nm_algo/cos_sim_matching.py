from typing import Any

from scipy.sparse.csr import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin
from sparse_dot_topn import awesome_cossim_topn


class SparseMatrixCosineSimTransformer(BaseEstimator, TransformerMixin):
    """
    Use cosine similarity to get topn candidate
    https://github.com/ing-bank/sparse_dot_topn
    """

    def __init__(self, top_n: int = 2, threshold: float = 0.01) -> None:
        """
        ntop: top n candidate
        lower_bound: a threshold that
        """
        self.top_n = top_n
        self.threshold = threshold

    def fit(self, X: Any, y: Any = None) -> "SparseMatrixCosineSimTransformer":
        return self

    def transform(
        self, gt_spr_mat: csr_matrix, nm_spr_mat: csr_matrix
    ) -> csr_matrix:
        """
        Input:
            gt_spr_mat: vector representation of groundtruth set in sparse matrix
            nm_spr_mat: vector representation of name matching set in sparse matrix

        Return: matched: a N*M sparse matrix
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

        """
        # N.B. nm_set sparse matrix need to be first
        matched = awesome_cossim_topn(
            nm_spr_mat, gt_spr_mat.T, self.top_n, self.threshold
        )
        return matched
