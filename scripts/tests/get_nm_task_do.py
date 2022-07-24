import sys

from server.api.main import app  # noqa: F401

# from server.api.main import app
from server.apps.nm_task.crud import NM_TASK_CRUD
from server.libs.db.sqlalchemy import db

if __name__ == "__main__":
    task_id = int(sys.argv[1])
    print("Batch name matching proc: task_id", task_id)

    with db():
        do_task = NM_TASK_CRUD.get_task(task_id)
        print(do_task)
