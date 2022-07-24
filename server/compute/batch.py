"""
This file contains real-time name matching main class and query API endpoint
"""
import sys
import time

# N.B. this FastAPI is just to enable db session middleware
from fastapi import FastAPI

from server.apps.nm_task.schemas import NM_STATUS
from server.compute.utils import change_task_status
from server.libs.db.sqlalchemy import (
    DBSessionMiddleware,
    db,
    engine,
    session_args,
)
from server.nm_algo.pipeline import NameMatchingBatch
from server.settings.logger import compute_logger as logger

app = FastAPI()

app.add_middleware(
    DBSessionMiddleware, custom_engine=engine, session_args=session_args
)

if __name__ == "__main__":
    task_id = int(sys.argv[1])
    user_id = int(sys.argv[2])
    logger.info(
        f"[Batch nm proc] received task_id [{task_id}] and user_id [{user_id}]"
    )

    with db():
        # the task status is changed to "launching" in "task start" endpoint
        start_t = time.time()

        nm_batch_task = NameMatchingBatch(task_id, user_id)
        logger.info(f"[Batch nm proc]: matching init\t {time.time() - start_t}")

        nm_batch_task.execute()
        logger.info(
            f"[Batch nm proc]: matchign finished in {time.time() - start_t,} seconds"
        )

        # setup up nm task status to terminating
        # the main process will setup status as terminated
        change_task_status(task_id, NM_STATUS.TERMINATING, "Batch nm proc")
        logger.info("[Batch nm proc]: nm task status switch to TERMINATING")
