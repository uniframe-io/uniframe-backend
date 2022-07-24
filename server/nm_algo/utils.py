import datetime
import logging
import subprocess
import uuid

import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.series import Series
from scipy.sparse.csr import csr_matrix

from server.apps.media.schemas import MEDIA_CONTENT_TYPE, MediaExtInfo
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schemas import AbcXyz_TYPE, BatchMatchingResult
from server.core.exception import EXCEPTION_LIB
from server.libs.fs.factory import FILE_STORE_FACTORY
from server.settings.global_sys_config import GLOBAL_CONFIG

MEM_USAGE_CMD = ["cat", "/sys/fs/cgroup/memory/memory.usage_in_bytes"]


def load_df(file_loc: str, media_type: MEDIA_CONTENT_TYPE) -> DataFrame:
    """
    Load file from file system location in nm_cfg to a pandas dataframe
    TODO: put it into platform factories, for S3 and local disk
    TODO: maximal file size???
    TODO: add exception
    """
    if media_type == MEDIA_CONTENT_TYPE.CSV:
        return pd.read_csv(file_loc)

    if media_type in [MEDIA_CONTENT_TYPE.XLS, MEDIA_CONTENT_TYPE.XLSX]:
        return pd.read_excel(file_loc)

    raise EXCEPTION_LIB.MEDIA__MIME_TYPE_ERROR.value(
        f"The data file [{file_loc}] content type is [{media_type}]. We only support CSV and EXCEL file"
    )


def save_result(task_id: int, user_id: int, result: DataFrame) -> None:
    """"""
    task_do = NM_TASK_CRUD.get_task(task_id)
    if task_do is None:
        raise EXCEPTION_LIB.TASK_COMPUTE__TASK_ID_NOT_CORRECT.value(
            f"Task id [{task_id} not found]"
        )

    if task_do.type != AbcXyz_TYPE.NAME_MATCHING_BATCH:
        raise EXCEPTION_LIB.TASK_COMPUTE__TASK_TYPE_NOT_EXPECTED.value(
            f"Task [{task_id}] is not a batch task!"
        )

    uuid_substr = str(uuid.uuid4())[:8]
    bucket_name = GLOBAL_CONFIG.bucket_name

    loc_prefix = FILE_STORE_FACTORY.generate_fs_prefix()
    location = f"{loc_prefix}/{bucket_name}/user={user_id}/tasks/task={task_id}/{task_id}-{uuid_substr}.csv"
    FILE_STORE_FACTORY.save_df(result, location)

    matching_result = BatchMatchingResult(
        location=location,
        ext_info=MediaExtInfo(
            header=result.columns.tolist(),
            first_n_rows=result.head(5).to_json(orient="records"),
            file_name=f"task_{task_id}.csv",
            media_type=MEDIA_CONTENT_TYPE.CSV,
        ),
    )
    task_do.ext_info.matching_result = matching_result  # type: ignore
    task_do.updated_at = datetime.datetime.utcnow()
    NM_TASK_CRUD.update_task(task_id, task_do)


def mem_usage_in_byte(logger: logging.Logger, info: str = "") -> None:
    mem_usage_rtv = subprocess.run(
        MEM_USAGE_CMD, stdout=subprocess.PIPE, text=True
    )
    mem_usage = mem_usage_rtv.stdout.rstrip()
    logger.debug(
        f"[memory probe] [{info}] current memory situation: {mem_usage}"
    )


def mem_probe_df(logger: logging.Logger, df: DataFrame, obj_name: str) -> None:
    logger.debug(
        f"[memory probe] {obj_name} uses {df.memory_usage(deep=True).sum()} bytes"
    )
    mem_usage_in_byte(logger, f"after {obj_name}")


def mem_probe_series(logger: logging.Logger, s: Series, obj_name: str) -> None:
    logger.debug(
        f"[memory probe] {obj_name} uses {s.memory_usage(deep=True)} bytes"
    )
    mem_usage_in_byte(logger, f"after {obj_name}")


def mem_probe_csr_matrix(
    logger: logging.Logger, mat: csr_matrix, obj_name: str
) -> None:
    mem = mat.data.nbytes + mat.indptr.nbytes + mat.indices.nbytes
    logger.debug(f"[memory probe] {obj_name} uses {mem} bytes")
    mem_usage_in_byte(logger, f"after {obj_name}")
