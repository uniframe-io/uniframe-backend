from typing import Any, List, Union

from pandas.core.frame import DataFrame
from pandas.core.series import Series
from scipy.sparse.csr import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from server.apps.nm_task import schemas
from server.core.exception import EXCEPTION_LIB
from server.nm_algo.cos_sim_matching import SparseMatrixCosineSimTransformer
from server.nm_algo.post_matching import (
    JoinGTInfoTransformer,
    PostProcessingTransformer,
)
from server.nm_algo.prepare_series import ExtractNameColTransformer
from server.nm_algo.preprocessing import PreprocessingPipeline
from server.nm_algo.utils import mem_probe_csr_matrix, mem_probe_series
from server.settings.logger import nm_algo_logger as logger


class Matcher(object):
    """
    Base Matcher
    """

    def __init__(
        self,
        nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        gt_df: DataFrame,
    ):
        """
        Input:
            - nm_cfg: name matching configuration
            - gt_df: groundtruth dataframe.
            N.B. here we pass the reference of gt_df
            TODO: test if there is any memory problem
        """
        self.nm_cfg = nm_cfg
        self.gt_df = gt_df
        self.prep_model = PreprocessingPipeline(self.nm_cfg.algorithm_option)
        return

    def extract_gt_name_col(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        force: bool,
    ) -> bool:
        """
        Extract name columns from search_option.search_key_gt
            if force=True, force to re-run
            if the configuraiton change, also need to re-run
        """
        if not force:
            if (
                self.nm_cfg.gt_dataset_config.search_key
                == curr_nm_cfg.gt_dataset_config.search_key
            ):
                return False

        self.extract_gt_name_model = ExtractNameColTransformer(
            curr_nm_cfg.gt_dataset_config.search_key
        )
        self.gt_name_series = self.extract_gt_name_model.transform(self.gt_df)
        mem_probe_series(logger, self.gt_name_series, "self.gt_name_series")

        return True

    def extract_nm_name_col(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        nm_df: DataFrame,
    ) -> Series:
        """
        Extract name columns from search_option.search_key_gt
        """
        if curr_nm_cfg.nm_dataset_config.search_key is None:  # type: ignore
            raise EXCEPTION_LIB.NM_ALGO__NO_NAME_COLUMN_INPUT.value(
                "Name matching set doesn't have search_key_nm"
            )
        return ExtractNameColTransformer(
            curr_nm_cfg.nm_dataset_config.search_key  # type: ignore
        ).transform(nm_df)

    def prep_gt(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        force: bool,
    ) -> bool:
        """
        preprocessing groundtruth data based on algorithm_option.value.preprocessing_option
            if force=True, force to re-run
            if the configuraiton change, also need to re-run
        """
        if not force:
            if (
                self.nm_cfg.algorithm_option.value.preprocessing_option
                == curr_nm_cfg.algorithm_option.value.preprocessing_option
            ):
                return False

        self.prep_model = PreprocessingPipeline(curr_nm_cfg.algorithm_option)
        self.gt_prep_series = self.prep_model.transform(
            self.gt_name_series, is_gt=True
        )

        mem_probe_series(logger, self.gt_prep_series, "self.gt_prep_series")

        return True

    def prep_nm(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        name_series: Series,
    ) -> Series:
        """
        preprocessing nm set
        """
        if self.prep_nm is None:
            raise EXCEPTION_LIB.NM_ALGO__PREPROCESSING_PIPELINE_NOT_INIT.value(
                "the preprocessing pipeline has not been initialized yet!"
            )
        return self.prep_model.transform(name_series, is_gt=False)

    def pre_match_gt(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        force: bool,
    ) -> bool:
        """
        prepare groundtruth set tensor
        """
        raise NotImplementedError("Must be implemented in the subclass")

    def pre_match_nm(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        nm_name_series: Series,
    ) -> Any:
        """
        prepare nm set tensor
        """
        raise NotImplementedError("Must be implemented in the subclass")

    def match(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        gt_tensor: Any,
        nm_tensor: Any,
    ) -> Any:
        """
        Matching: find the topN similarity
        """
        raise NotImplementedError("Must be implemented in the subclass")

    def post_match(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        matched: Any,
        nm_name_series: Series,
    ) -> Any:
        """
        Post matching
        """
        raise NotImplementedError("Must be implemented in the subclass")


class EditDistanceMatcher(Matcher):
    def __init__(
        self,
        nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        gt_df: DataFrame,
    ):
        # TODO: think about how to add exception
        # if nm_cfg.algorithm_option.type != AlgorithmOptionType.EDIT_DISTANCE:
        #     raise EXCEPTION_LIB.NM_ALGO__MATCHER_INCOMPATIBLE.value(
        #         "EditDistanceMatcher initiate error. The configuration is not for EditDistanceMatcher"
        #     )
        super().__init__(nm_cfg, gt_df)

    def pre_match_gt(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        force: bool,
    ) -> bool:
        """
        Placeholder step.
        Edit distance just use string
        """
        # identified pre-match layer
        self.gt_tensor = self.gt_prep_series
        return force

    def pre_match_nm(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        nm_name_series: Series,
    ) -> Series:
        """
        Placeholder step.
        Edit distance just use string
        """
        # identified pre-match layer
        return nm_name_series

    def match(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        gt_tensor: Series,
        nm_tensor: Series,
    ) -> List:
        # TODO: To be added
        return []

    def post_match(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        matched: Any,
        nm_name_series: Series,
    ) -> List:
        # TODO: To be added
        return []


class VectorExactMatcher(Matcher):
    def __init__(
        self,
        nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        gt_df: DataFrame,
    ):
        # TODO: fix the union mypy error later
        # if (
        #     nm_cfg.algorithm_option.type == AlgorithmOptionType.EDIT_DISTANCE
        #     or nm_cfg.algorithm_option.value.cos_match_type
        #     != CosineMatchingType.EXACT
        # ):
        #     raise EXCEPTION_LIB.NM_ALGO__MATCHER_INCOMPATIBLE.value(
        #         "VectorExactMatcher initiate error. The configuration is not for VectorExactMatcher"
        #     )
        super().__init__(nm_cfg, gt_df)

    def pre_match_gt(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        force: bool,
    ) -> bool:
        """
        prepare groundtruth set tensor
            if force=True, force to re-run
            if the configuraiton change, also need to re-run
        """
        curr_tokenizer_option = (
            curr_nm_cfg.algorithm_option.value.tokenizer_option  # type: ignore
        )
        if not force:
            if (
                self.nm_cfg.algorithm_option.value.tokenizer_option  # type: ignore
                == curr_tokenizer_option
            ):
                return False

        if curr_tokenizer_option == schemas.TokenizerType.WORD:  # type: ignore
            # N.B. the season we choose ngram_range = (1, 2):
            # if matching set has unknown words, tfidf-vectorizer will just ignore it.
            # Then, a stirng like "Zhe UNKNOWN Sun" will match with "Zhe Sun" with score 1
            # The best way is figure out how to handle UNKNOWN word in sklearn
            # Before we find the fix, we use 2-gram to compensate and lower the score of unknown word
            # 2021-11-07 update: fixed by normalize nm transform vector

            # self.pre_match_model = CountVectorizer(
            #     ngram_range=(1, 2), analyzer="word"
            # )

            self.pre_match_model = TfidfVectorizer(
                ngram_range=(1, 1), analyzer="word"  # , use_idf=False
            )

        elif curr_tokenizer_option == schemas.TokenizerType.SUBWORDE:
            # char_wb is better than char
            self.pre_match_model = TfidfVectorizer(
                ngram_range=(3, 3), analyzer="char_wb"  # , use_idf=False
            )

        else:
            logger.error(
                f"TASK__WRONG_TOKENIZATION_OPTION: get input tokenizer_option [{curr_tokenizer_option}]"
            )
            raise EXCEPTION_LIB.TASK__WRONG_TOKENIZATION_OPTION.value(
                f"Your input of tokenization option is [{curr_tokenizer_option}], which we don't support"
            )

        # analyzer is used to prep matching set
        self.analyzer = self.pre_match_model.build_analyzer()

        self.gt_tensor = self.pre_match_model.fit_transform(self.gt_prep_series)

        mem_probe_csr_matrix(logger, self.gt_tensor, "self.gt_tensor")

        return True

    def pre_match_nm(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        name_series: Series,
    ) -> csr_matrix:
        """
        prepare nm set tensor
        """

        matching_set_tfidf = self.pre_match_model.transform(name_series)

        # get non zero count per row
        ind_pointer_array = matching_set_tfidf.indptr
        non_zero_cnt = ind_pointer_array[1:] - ind_pointer_array[:-1]

        # we need to compensate the unknown token
        # otherwise, a stirng like "Zhe UNKNOWN Sun" will match with "Zhe Sun" with score 1
        for idx, name in enumerate(name_series):
            name_tokens = self.analyzer(name)
            len_tokens = len(set(name_tokens))
            # len_words_out_voc = len_tokens - non_zero_cnt[idx]

            matching_set_tfidf[idx] = (
                matching_set_tfidf[idx] * non_zero_cnt[idx] / len_tokens
            )

        return matching_set_tfidf

    def match(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        gt_tensor: csr_matrix,
        nm_tensor: csr_matrix,
    ) -> csr_matrix:
        """
        Do the real top N similarity selection based on the cosine similarity
        We use this package https://github.com/ing-bank/sparse_dot_topn
        """
        cos_sim_transformer = SparseMatrixCosineSimTransformer(
            top_n=curr_nm_cfg.search_option.top_n,
            threshold=curr_nm_cfg.search_option.threshold,
        )
        matched = cos_sim_transformer.transform(gt_tensor, nm_tensor)
        mem_probe_csr_matrix(logger, matched, "matched")
        return matched

    def post_match(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        matched: csr_matrix,
        nm_name_series: Series,
    ) -> DataFrame:
        """
        post matching:
        - join the result with the groundtruth name
        """
        list_result = JoinGTInfoTransformer().transform(
            matched, self.gt_name_series
        )

        gt_df_sub = None
        if len(curr_nm_cfg.search_option.selected_cols) > 0:
            # TODO: add gt column selection exception
            gt_df_sub = self.gt_df[curr_nm_cfg.search_option.selected_cols]

        return PostProcessingTransformer().transform(
            list_result, nm_name_series, gt_df_sub
        )


class VectorApproximateMatcher(Matcher):
    def __init__(
        self,
        nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        gt_df: DataFrame,
    ):
        # TODO: fix the union mypy error later
        # if (
        #     nm_cfg.algorithm_option.type == AlgorithmOptionType.EDIT_DISTANCE
        #     or nm_cfg.algorithm_option.value.cos_match_type
        #     != CosineMatchingType.APPROXIMATE
        # ):
        #     raise EXCEPTION_LIB.NM_ALGO__MATCHER_INCOMPATIBLE.value(
        #         "VectorApproximateMatcher initiate error. The configuration is not for VectorApproximateMatcher"
        #     )

        super().__init__(nm_cfg, gt_df)

    def pre_match_gt(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        force: bool,
    ) -> bool:
        # TODO: add the real implementation
        self.gt_tensor = self.gt_prep_series
        return False

    def pre_match_nm(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        nm_name_series: Series,
    ) -> Series:
        # TODO: add the real implementation
        return nm_name_series

    def match(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        gt_tensor: Series,
        nm_tensor: Series,
    ) -> List:
        # TODO: add the real implementation
        return []

    def post_match(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        matched: Any,
        nm_name_series: Series,
    ) -> Any:
        # TODO: add the real implementation
        return []
