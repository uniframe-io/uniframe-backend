from scripts.tests.nm_task_helper import (
    create_dataset,
    create_dummy_user,
    create_media_gt_small,
    create_realtime_nm_task,
)
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.compute.rq_worker import run_task_in_subprocess
from server.compute.utils import get_q
from server.libs.db.sqlalchemy import db


def run() -> None:
    with db():

        do_user = create_dummy_user()
        do_media_gt = create_media_gt_small(do_user)
        do_dataset_gt = create_dataset(do_user, "gt_small_set", do_media_gt)
        do_realtime_task = create_realtime_nm_task(do_user, do_dataset_gt)

        q = get_q("nm_realtime_worker")
        q.enqueue(
            run_task_in_subprocess,
            (
                do_realtime_task.id,
                NM_TASK_CRUD,
                [
                    "uvicorn",
                    "server.compute.realtime:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8001",
                ],
            ),
            job_id="nm_realtime_task",
            job_timeout=-1,
        )


if __name__ == "__main__":
    run()
