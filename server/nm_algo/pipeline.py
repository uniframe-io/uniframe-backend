import gc
from typing import Any, List, Union

import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.series import Series

from server.apps.nm_task import schemas
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schemas import (
    AbcXyz_TYPE,
    AlgorithmOptionType,
    CosineMatchingType,
)
from server.core.exception import EXCEPTION_LIB
from server.nm_algo.matcher import (
    EditDistanceMatcher,
    VectorApproximateMatcher,
    VectorExactMatcher,
)
from server.nm_algo.prepare_series import (
    LoadGtSetTransformer,
    LoadNmSetTransformer,
)
from server.nm_algo.utils import (
    mem_probe_csr_matrix,
    mem_probe_df,
    mem_probe_series,
    mem_usage_in_byte,
    save_result,
)
from server.settings.logger import nm_algo_logger as logger

"""
Name Matching pipeline. The actual running of batch and realtime matching will use this class

Example:
```
nm_rt_task = NameMatchingRealtime(nm_cfg_id="rt-2021-01-19-22-10-12-b7e7407a-5a9a-11eb-8c4c-acde48001122")
rtv = nm_rt_task.execute(["Zhe Sun"])
print(rtv)
```
"""


class NameMatchingBase(object):
    def __init__(
        self, nm_task_id: int, user_id: int, expected_type: AbcXyz_TYPE
    ):
        """
        Name Matching Base class
        nm_task_id: name matching task id
        """
        mem_usage_in_byte(logger, "start nm pipeline")

        self.nm_task_id = nm_task_id
        self.user_id = user_id

        nm_task = NM_TASK_CRUD.get_task(self.nm_task_id)
        if nm_task is None:
            raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
                f"The name matching task_id {nm_task_id} does not exist"
            )

        if nm_task.type != expected_type:
            raise EXCEPTION_LIB.NM_ALGO__NAME_MATCHING_TYPE_ERROR.value(
                "NameMatching type does not match!"
            )

        self.nm_task = nm_task
        self.nm_cfg = nm_task.ext_info

        # Load groundtruth data
        self.load_gt(self.nm_cfg.gt_dataset_config.dataset_id)

        # initialize different type of matcher
        self.edit_distance_matcher = EditDistanceMatcher(
            self.nm_cfg, self.gt_df
        )
        self.vector_exact_matcher = VectorExactMatcher(self.nm_cfg, self.gt_df)
        self.vector_approx_matcher = VectorApproximateMatcher(
            self.nm_cfg, self.gt_df
        )

        # assign a working matcher according to the configuration
        self.matcher: Union[
            EditDistanceMatcher, VectorExactMatcher, VectorApproximateMatcher
        ]
        self.update_matcher(self.nm_cfg)

        # run the groundtruth preparation pipeline when initiate the class
        self.run_gt_pipeline(self.nm_cfg, force=True)

        # free memory explictly
        gc.collect()
        mem_usage_in_byte(logger, "finish GT pipeline")

        return

    def load_gt(self, gt_data_id: int) -> None:
        """
        Load groundtruth data according to the configuration
        """
        self.gt_df = LoadGtSetTransformer(gt_data_id).transform()
        mem_probe_df(logger, self.gt_df, "self.gt_df")

    def update_matcher(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
    ) -> bool:
        """
        Update the matcher

        Return: bool, if the following pipeline needs to be executed enforced
                if the matcher configuration change, the following pipeline has to be re-run
        """
        if (
            curr_nm_cfg.algorithm_option.type
            == AlgorithmOptionType.EDIT_DISTANCE
        ):
            self.matcher = self.edit_distance_matcher
            return (
                curr_nm_cfg.algorithm_option.type
                != self.nm_cfg.algorithm_option.type
            )
        else:
            if (
                curr_nm_cfg.algorithm_option.value.cos_match_type  # type: ignore
                == CosineMatchingType.EXACT
            ):
                self.matcher = self.vector_exact_matcher
            else:
                self.matcher = self.vector_approx_matcher

            return (
                curr_nm_cfg.algorithm_option.value.cos_match_type  # type: ignore
                != self.nm_cfg.algorithm_option.value.cos_match_type  # type: ignore
            )

    def run_gt_pipeline(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        force: bool = False,
    ) -> None:
        """
        Run the pipeline for prepare the pipeline, including:
          - extract the groundtruch name colums from the configuration
          - preproces the grountruth data according to the configuration
          - prepare the groundtruth tensor for matching

        Input:
          - curr_nm_cfg: name matching task configuration
          - force: if pipeline is run enforced

        N.B. if one step runs, all following components must run no matter their condiction function result
        """
        conditional_pipeline = [
            self.matcher.extract_gt_name_col,
            self.matcher.prep_gt,
            self.matcher.pre_match_gt,
        ]

        force_run_flag = force
        for step in conditional_pipeline:
            force_run_flag = step(curr_nm_cfg, force_run_flag)

    def transform(
        self,
        curr_nm_cfg: Union[schemas.NmCfgBatchSchema, schemas.NmCfgRtSchema],
        nm_name_series: Series,
    ) -> DataFrame:
        """
        Run the rest of the name matching pipeline, after `run_gt_pipeline`, including
          - preprocossing name matching according to the configuration
          - prepare the name matching set tensor
          - do the match
          - post match processing, such as join back names
        """
        raw_nm_name_seires = nm_name_series.copy()
        nm_name_prep_series = self.matcher.prep_nm(curr_nm_cfg, nm_name_series)
        mem_probe_series(logger, nm_name_prep_series, "nm_name_prep_series")

        nm_tensor = self.matcher.pre_match_nm(curr_nm_cfg, nm_name_prep_series)
        mem_probe_csr_matrix(logger, nm_tensor, "nm_tensor")

        # ----- free memory explictly ----
        gc.collect()
        mem_usage_in_byte(logger, "finish nm csr mat preparation")
        # ---------------------------------

        matched = self.matcher.match(
            curr_nm_cfg, self.matcher.gt_tensor, nm_tensor
        )

        final_result = self.matcher.post_match(
            curr_nm_cfg, matched, raw_nm_name_seires
        )
        mem_usage_in_byte(logger, "finish matching")

        # ----- free memory explictly ----
        gc.collect()
        # ---------------------------------

        return final_result


class NameMatchingBatch(NameMatchingBase):
    """
    Sub-class for the batch scenario
    """

    def __init__(self, nm_task_id: int, user_id: int) -> None:
        super().__init__(
            nm_task_id, user_id, expected_type=AbcXyz_TYPE.NAME_MATCHING_BATCH
        )

    def load_nm(
        self,
        nm_data_id: int,
    ) -> None:
        """
        Load name matching set to dataframe
        """
        self.nm_df = LoadNmSetTransformer(nm_data_id).transform()

        mem_probe_df(logger, self.nm_df, "self.nm_df")

    def execute(self) -> Any:
        """
        Trigger the matching action
        """
        self.load_nm(self.nm_cfg.nm_dataset_config.dataset_id)  # type: ignore
        nm_name_series = self.matcher.extract_nm_name_col(
            self.nm_cfg, self.nm_df
        )
        mem_probe_series(logger, nm_name_series, "nm_name_series")

        # ----- free memory explictly ----
        gc.collect()

        self.result = self.transform(self.nm_cfg, nm_name_series)

        save_result(self.nm_task_id, self.user_id, self.result)
        mem_usage_in_byte(logger, "finish saving result and db")

        return self.result


class NameMatchingRealtime(NameMatchingBase):
    """
    Sub-class for the realtime scenario
    """

    def __init__(self, nm_task_id: int, user_id: int) -> None:
        super().__init__(
            nm_task_id,
            user_id,
            expected_type=AbcXyz_TYPE.NAME_MATCHING_REALTIME,
        )

    def execute(self, query_l: List[str]) -> DataFrame:
        """
        Trigger the matching action
        """

        # N.B. Here we get the latest task configuration
        # then, we check if we need to choose a new matcher and re-run the groudtruth pipeline
        logger.info("start matching")
        logger.info(self.nm_task)
        nm_task = NM_TASK_CRUD.get_task(self.nm_task_id)
        logger.info("Retrieve nm_task")

        if nm_task is None:
            logger.info("TASK__CURRENT_TASK_NOT_EXIST")
            logger.info(self.nm_cfg)
            raise EXCEPTION_LIB.TASK__CURRENT_TASK_NOT_EXIST.value(
                f"The name matching task_id {self.nm_task_id} does not exist"
            )
        curr_nm_cfg = nm_task.ext_info

        force_flag = self.update_matcher(curr_nm_cfg)
        self.run_gt_pipeline(curr_nm_cfg, force=force_flag)
        mem_usage_in_byte(logger, "complete run_gt_pipeline")

        nm_name_series = pd.Series(query_l)
        result = self.transform(curr_nm_cfg, nm_name_series)
        mem_usage_in_byte(logger, "complete matching")

        # update the nm_cfg by the latest nm_cfg
        self.nm_cfg = curr_nm_cfg

        # ----- free memory explictly ----
        mem_usage_in_byte(logger, "final usage for this search round")
        # ---------------------------------

        return result
