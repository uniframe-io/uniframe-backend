"""
This file contains real-time name matching main class and query API endpoint
"""
import os
import sys
from typing import List

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from server.apps.nm_task.schemas import NM_STATUS, RTQueryResp
from server.compute.utils import change_task_status
from server.libs.db.sqlalchemy import (
    DBSessionMiddleware,
    db,
    engine,
    session_args,
)
from server.nm_algo.pipeline import NameMatchingRealtime
from server.settings import API_SETTING
from server.settings.logger import compute_logger as logger

# def refactor_match_result(
#     raw_result: Optional[List],
# ) -> Optional[List[MatchResult]]:
#     """
#     Reshape the nm result

#     if has matched result
#         - from [(row_id, matched_str, score)]
#         - to [MatchResult]
#     if no matching result
#         - raw_result is None, retrun a empty list []
#     """
#     if raw_result is None:
#         return []

#     return [
#         MatchResult(matched_str=r[1], row_id=r[0], similarity_score=r[2])
#         for r in raw_result
#     ]


app = FastAPI()

origin_list = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    DBSessionMiddleware, custom_engine=engine, session_args=session_args
)


@app.get(
    f"{API_SETTING.API_V1_STR}/heartbeat",
    summary="Heartbeat endpoint for name matching real-time query",
    response_model=str,
    response_description="the heartbeat response",
)
def heartbeat() -> str:
    return "healthy"


@app.get(
    f"{API_SETTING.API_V1_STR}/nm-realtime",
    summary="Name matching real-time query",
    response_model=RTQueryResp,
    response_description="The matching result of the query string(s)",
)
def nm_rt(q: List[str] = Query([])) -> RTQueryResp:
    """Real-time query

    - **q**: list of query string, defaults to Query([]), _type q: List[str], optional_
    """
    if q:
        nm_result = nm_rt_task.execute(q)
        # query_result = [
        #     RTQueryResp(query_key=keyword, match_list=refactor_match_result(r))
        #     for keyword, r in zip(q, nm_result)
        # ]
        query_result = nm_result.values.tolist()
    else:
        query_result = []

    resp = RTQueryResp(
        query_result=query_result,
        columns=nm_result.columns.tolist(),
        search_option=nm_rt_task.nm_cfg.search_option,
    )

    return resp


task_id = os.getenv("NM_TASK_ID")
if task_id is None:  # type: ignore
    sys.exit("[Realtime nm proc] Must setup NM_TASK_ID")

user_id = os.getenv("USER_ID")
if user_id is None:  # type: ignore
    sys.exit("[Realtime nm proc] Must setup USER_ID")


task_id = int(task_id)  # type: ignore
user_id = int(user_id)  # type: ignore
logger.info(f"[Realtime nm proc] task_id [{task_id}] user_id [{user_id}]")

with db():
    # the task status is changed to "launching" in "task start" endpoint

    nm_rt_task = NameMatchingRealtime(task_id, user_id)  # type: ignore

    change_task_status(task_id, NM_STATUS.READY, "Realtime nm proc")  # type: ignore
    logger.info("[Realtime nm proc]: nm task status switch to READY")
