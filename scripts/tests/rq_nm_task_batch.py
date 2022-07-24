from scripts.tests.nm_task_helper import (
    create_batch_nm_task,
    create_dataset,
    create_dummy_user,
    create_media_gt_small,
    create_media_nm_small,
)
from server.api.main import app  # noqa: F401
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.compute.rq_worker import run_task_in_subprocess
from server.compute.utils import get_q
from server.libs.db.sqlalchemy import db


def run() -> None:
    with db():

        do_user = create_dummy_user()
        do_media_gt = create_media_gt_small(do_user)
        do_media_nm = create_media_nm_small(do_user)

        do_dataset_gt = create_dataset(do_user, "gt_small_set", do_media_gt)
        do_dataset_nm = create_dataset(do_user, "nm_small_set", do_media_nm)

        do_batch_task = create_batch_nm_task(
            do_user, do_dataset_gt, do_dataset_nm
        )

        q = get_q("nm_batch_worker")
        q.enqueue(
            run_task_in_subprocess,
            (
                do_batch_task.id,
                NM_TASK_CRUD,
                ["python", "server/compute/batch.py", f"{do_batch_task.id}"],
            ),
            job_id="nm_batch_task",
            job_timeout=-1,
        )


if __name__ == "__main__":
    run()
