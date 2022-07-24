from datetime import datetime
from typing import Optional

import redis
import rq

from server.apps.nm_task.crud import NM_TASK_CRUD
from server.apps.nm_task.schemas import NM_STATUS
from server.core.exception import EXCEPTION_LIB
from server.settings import API_SETTING
from server.settings.logger import compute_logger as logger
from server.utils.k8s_resource_name import gen_k8s_resource_prefix


def change_task_status(
    task_id: int,
    task_status: NM_STATUS,
    log_info: str,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
) -> None:
    logger.info(
        f"Attempting [{log_info}] {task_id} change status to [{task_status}]"
    )

    task_do = NM_TASK_CRUD.get_task(task_id)
    if task_do is None:
        logger.error(
            f"TASK_COMPUTE__TASK_ID_NOT_CORRECT: Input task id {task_id} does not exist! task_status [{task_status}]"
        )
        raise EXCEPTION_LIB.TASK_COMPUTE__TASK_ID_NOT_CORRECT.value(
            f"Input task id {task_id} does not exist!"
        )

    task_do.ext_info.nm_status = task_status
    task_do.updated_at = datetime.utcnow()

    if started_at:
        task_do.started_at = started_at

    if finished_at:
        task_do.finished_at = finished_at
    else:
        # N.B. if finished is None, it means a new running round, and task just start and not finished yet.
        task_do.finished_at = None

    NM_TASK_CRUD.update_task(task_id, task_do)
    logger.info(
        f"[{log_info}] {task_id} changed status to [{task_status}] at {task_do.updated_at}"
    )


def get_task_computation_config(task_id: int) -> dict:
    task_do = NM_TASK_CRUD.get_task(task_id)
    if task_do is None:
        logger.error(
            f"TASK_COMPUTE__TASK_ID_NOT_CORRECT: Input task id {task_id} does not exist!"
        )
        raise EXCEPTION_LIB.TASK_COMPUTE__TASK_ID_NOT_CORRECT.value(
            f"Input task id {task_id} does not exist!"
        )
    return task_do.ext_info.computation_resource.computation_config.dict()


def get_q(queue_name: str) -> rq.Queue:
    """
    Get RQ work queue
    ONLY in ECS and docker-composer mode
    """
    redis_conn = redis.Redis(host=API_SETTING.REDIS_DNS, port=6379, db=0)
    return rq.Queue(queue_name, connection=redis_conn)


def gen_pubsub_channel_name(task_id: int, user_id: int) -> str:
    return f"{gen_k8s_resource_prefix(task_id, user_id)}-channel"


# SessionLocal = scoped_session(
#     sessionmaker(
#         autocommit=False,
#         autoflush=False,
#         expire_on_commit=False,
#         bind=engine,
#     )
# )

# session_local = SessionLocal()


# @contextmanager
# def session_maker(session: Any = session_local) -> Any:
#     """
#     Session maker make session closed automatically

#     @param session:
#     @return:
#     """
#     try:
#         yield session
#         session.commit()
#     except Exception as exc:
#         # if other exception, override by Nm Exceptions
#         session.rollback()
#         traceback.print_exc()
#         raise EXCEPTION_LIB.DB__CRUD_SQLAlCHEMY_ERROR.value(
#             f"Get SQLAlchemyError. Exception message: {exc}"
#         )
#     finally:
#         session.close()
