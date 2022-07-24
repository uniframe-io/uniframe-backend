from functools import reduce
from typing import Any, List, Union

from pandas.core.frame import DataFrame
from pandas.core.series import Series
from sklearn.base import BaseEstimator, TransformerMixin

from server.apps.dataset.crud import DATASET_CRUD
from server.apps.media.crud import MEDIA_CRUD
from server.core.exception import EXCEPTION_LIB
from server.nm_algo.utils import load_df


class LoadGtSetTransformer(BaseEstimator, TransformerMixin):
    """
    Load groundtruth dataset from nm task configuration
    """

    def __init__(self, gt_data_id: int) -> None:
        """
        nm_cfg: name matching task configuration
        """

        gt_dataset_do = DATASET_CRUD.get_dataset(gt_data_id)
        if gt_dataset_do is None:
            raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
                f"In batch name matching LoadGtSetTransformer, groundtruth dataset {gt_data_id} does not exist"
            )
        self.gt_dataset_do = gt_dataset_do

        gt_media_do = MEDIA_CRUD.get_media(self.gt_dataset_do.media_id)
        if gt_media_do is None:
            raise EXCEPTION_LIB.MEDIA__CURRENT_MEDIA_NOT_EXIST.value(
                f"In batch name matching LoadGtSetTransformer, media {self.gt_dataset_do.media_id} of dataset {gt_data_id} does not exist"
            )
        self.gt_media_do = gt_media_do

    def fit(self) -> None:
        """
        placeholder method, since it is just a transformer
        """
        return

    def transform(self) -> DataFrame:
        """
        Load groundtruth dataset from nm task configuration
        """
        gt_loc = self.gt_media_do.location
        media_type = self.gt_media_do.ext_info.media_type

        if gt_loc is None:
            raise EXCEPTION_LIB.NM_CFG__GROUND_TRUTH_LOC_ERROR.value(
                "gt_config.location should not be None when start name matching"
            )
        return load_df(gt_loc, media_type)


class LoadNmSetTransformer(BaseEstimator, TransformerMixin):
    """
    Load name matching dataset from nm task configuration
    """

    def __init__(self, nm_data_id: int) -> None:
        """
        nm_cfg: name matching task configuration
        """
        nm_dataset_do = DATASET_CRUD.get_dataset(nm_data_id)
        if nm_dataset_do is None:
            raise EXCEPTION_LIB.DATASET__CURRENT_DATASET_NOT_EXIST.value(
                f"In batch name matching LoadNmSetTransformer, name matching dataset {nm_data_id} does not exist"
            )
        self.nm_dataset_do = nm_dataset_do

        nm_media_do = MEDIA_CRUD.get_media(self.nm_dataset_do.media_id)
        if nm_media_do is None:
            raise EXCEPTION_LIB.MEDIA__CURRENT_MEDIA_NOT_EXIST.value(
                f"In batch name matching LoadNmSetTransformer, media {self.nm_dataset_do.media_id} of dataset {nm_data_id} does not exist"
            )
        self.nm_media_do = nm_media_do

    def fit(self) -> None:
        """
        placeholder method, since it is just a transformer
        """
        return

    def transform(self) -> DataFrame:
        """
        Load name matching dataset from nm task configuration
        """
        nm_set_loc = self.nm_media_do.location
        media_type = self.nm_media_do.ext_info.media_type

        if nm_set_loc is None:
            raise EXCEPTION_LIB.NM_CFG__NM_SET_LOC_ERROR.value(
                "nm_set_config.location should not be None in Batch mode"
            )

        return load_df(nm_set_loc, media_type)


class ExtractNameColTransformer(BaseEstimator, TransformerMixin):
    """
    This transformer class build a name column by given columns list

    Example:
    ```
        df = pd.DataFrame({"name_1": ["Amsterdam", "Utrecht"], "name_2":["BV", "NV"]})
        result = ExtractNameColTransformer(["name_1", "name_2"]).transform(df)
        print(result)

        ["Amsterdam BV", "Utrecht NV"]
    ```

    There is another way to implement transformer by sklearn.processing.FunctionTransformer
    But the input argument is a bit urgly, if we want to use transformer in the pipeline.
    There is a workaround (https://ig248.gitlab.io/post/2018-11-21-transformer-factory/), but the implementation is complicated

    In NM algorithm, we use BaseEstimator for estimator and transformer with parameters
    ``` python
    def extract_name_columns(df: DataFrame, name_col_l: List[str]):
        if len(name_col_l) == 0:
            raise EXCEPTION_LIB.NM_ALGO__NO_NAME_COLUMN_INPUT.value("No name columns input")

        if len(name_col_l) > 1:
            for col in name_col_l:
                if col not in df.columns:
                    raise EXCEPTION_LIB.NM_ALGO__NAME_COLUMN_NOT_IN_INPUT_DATA(f"Column [{col}] is not in the give data")

        name_col = reduce(lambda a, b: a + ' ' + b, (df[col] for col in name_col_l))
        return name_col


    concat_columns_transformer = FunctionTransformer(extract_name_columns, kw_args={"name_col_l": ["col1", "col2", "col3", "col1_prep"]})
    ```
    """

    def __init__(self, name_col_l: Union[str, List[str]]) -> None:
        """
        name_col_l: list of column which to be combined
        """

        if isinstance(name_col_l, str):
            self.name_col_l = [name_col_l]
        elif isinstance(name_col_l, list):
            self.name_col_l = name_col_l
        else:
            raise EXCEPTION_LIB.NM_ALGO__NO_NAME_COLUMN_INPUT.value(
                f"Name column should be either string or a list of string. The input is {type(name_col_l)}"
            )

    def fit(self, X: Any, y: Any = None) -> "ExtractNameColTransformer":
        """
        placeholder method, since it is just a transformer
        """
        return self

    def transform(self, df: DataFrame, y: Any = None) -> Series:
        """
        combine the columns
        """
        if len(self.name_col_l) == 0:
            raise EXCEPTION_LIB.NM_ALGO__NO_NAME_COLUMN_INPUT.value(
                "No name columns input"
            )

        if len(self.name_col_l) >= 1:
            for col in self.name_col_l:
                if col not in df.columns:
                    raise EXCEPTION_LIB.NM_ALGO__NAME_COLUMN_NOT_IN_INPUT_DATA.value(
                        f"Column [{col}] is not in the give data"
                    )

        name_col = reduce(
            lambda a, b: a + " " + b, (df[col] for col in self.name_col_l)
        )
        return name_col
