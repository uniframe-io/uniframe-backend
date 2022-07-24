import datetime
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import exc, true

from server.apps.nm_task import models
from server.apps.nm_task.schema_converter import NmTaskSchemaConvert
from server.apps.nm_task.schemas import (
    POD_STATUS,
    AbcXyz_TYPE,
    NmTaskCreateDO,
    NmTaskDO,
)
from server.core.exception import EXCEPTION_LIB
from server.libs.db.sqlalchemy import db
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_nm_task_logger as logger


class NmTaskCrudAbsFactory(ABC):
    """Abstract factory class for Name matching configuration"""

    @abstractmethod
    def create_task(
        self,
        nm_task: NmTaskCreateDO,
        user_id: int,
    ) -> NmTaskDO:
        pass

    @abstractmethod
    def get_task(self, abcxyz_id: int) -> Optional[NmTaskDO]:
        pass

    @abstractmethod
    def get_all_tasks_by_owner(self, owner_id: int) -> List[NmTaskDO]:
        pass

    @abstractmethod
    def get_tasks_by_owner(
        self, owner_id: int, task_type: AbcXyz_TYPE
    ) -> List[NmTaskDO]:
        pass

    @abstractmethod
    def get_task_by_name_type(
        self, user_id: int, name: str, task_type: AbcXyz_TYPE
    ) -> Optional[NmTaskDO]:
        pass

    @abstractmethod
    def update_task(self, abcxyz_id: int, nm_task: NmTaskDO) -> None:
        pass

    @abstractmethod
    def deactivate_task(self, abcxyz_id: int) -> None:
        pass

    @abstractmethod
    def delete_task(self, abcxyz_id: int) -> None:
        pass

    @abstractmethod
    def get_owner_id_by_task_id(self, abcxyz_id: int) -> Optional[int]:
        pass

    @abstractmethod
    def add_task_run_record(
        self, user_id: int, abcxyz_id: int, pod_name: str
    ) -> None:
        pass

    @abstractmethod
    def update_task_run_record_by_id(
        self,
        run_id: int,
        pod_status: POD_STATUS,
        finished_at: datetime.datetime,
    ) -> None:
        pass

    @abstractmethod
    def update_task_run_record(
        self,
        user_id: int,
        task_id: int,
        pod_name: str,
        pod_status: POD_STATUS,
        finished_at: datetime.datetime,
    ) -> None:
        pass

    @abstractmethod
    def get_all_running_task_pod(self) -> List[models.AbcXyzTaskRunHistory]:
        pass

    @abstractmethod
    def get_records_by_started_at(
        self, user_id: int, oldest_started_at: datetime.datetime
    ) -> List[models.AbcXyzTaskRunHistory]:
        pass

    @abstractmethod
    def get_task_run_history_list(
        self, user_id: int, abcxyz_id: int
    ) -> List[models.AbcXyzTaskRunHistory]:
        pass

    @abstractmethod
    def delete_task_by_owner(self, owner_id: int) -> None:
        pass

    @classmethod
    def make_concrete(cls) -> "NmTaskCrudAbsFactory":
        """The factory method to load name matching metadata factory"""

        NM_TASK_FACTORY_DICT = {"pg": PGNmTaskCRUD}

        return NM_TASK_FACTORY_DICT[GLOBAL_CONFIG.api_store]()


class PGNmTaskCRUD(NmTaskCrudAbsFactory):
    """Nm Task factory: PG Database system

    :param NmTaskCrudAbsFactory: abstract class, define the factory interface
    """

    def create_task(
        self,
        nm_task: NmTaskCreateDO,
        user_id: int,
    ) -> NmTaskDO:
        """"""
        po_task = models.AbcXyzTask(
            owner_id=user_id,
            name=nm_task.name,
            description=nm_task.description,
            is_public=False,
            is_active=True,
            type=nm_task.type,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            started_at=None,
            finished_at=None,
            ext_info=nm_task.ext_info.json(),
        )

        try:
            db.session.add(po_task)
            db.session.commit()
        except exc.IntegrityError:
            # the owner_id is a foreign key of users table
            # owner_id must be a valid user id which exists in user table
            # otherwise, an IntegrityError is raise
            db.session.rollback()
            logger.error(
                f"TASK__TASK_OWNER_ID_NOT_IN_USER_TABLE: owner_id [{user_id}]"
            )
            raise EXCEPTION_LIB.TASK__TASK_OWNER_ID_NOT_IN_USER_TABLE.value(
                "The current login user is not in users table. Please logout and retry"
            )

        db.session.refresh(po_task)

        if po_task is None:
            logger.error(
                f"TASK__CREATE_FAILED: Create Task in database failed! owner_id [{user_id}] name[{nm_task.name}] type[{nm_task.type}]"
            )
            raise EXCEPTION_LIB.TASK__CREATE_FAILED.value(
                "Create Task in database failed. Please contact the administrator"
            )

        return NmTaskSchemaConvert.task_po_2_do(po_task)

    def get_task(self, abcxyz_id: int) -> Optional[NmTaskDO]:
        po_task = (
            db.session.query(models.AbcXyzTask)
            .filter(models.AbcXyzTask.id == abcxyz_id)
            .filter(models.AbcXyzTask.is_active == true())
            .first()
        )
        if not po_task:
            return None

        do_task = NmTaskSchemaConvert.task_po_2_do(po_task)
        return do_task

    def get_tasks_by_owner(
        self, owner_id: int, task_type: AbcXyz_TYPE
    ) -> List[NmTaskDO]:
        po_tasks = (
            db.session.query(models.AbcXyzTask)
            .filter(models.AbcXyzTask.is_active == true())
            .filter(models.AbcXyzTask.owner_id == owner_id)
            .filter(models.AbcXyzTask.type == task_type)
            .all()
        )
        do_tasks = [NmTaskSchemaConvert.task_po_2_do(t) for t in po_tasks]
        return do_tasks

    def get_all_tasks_by_owner(self, owner_id: int) -> List[NmTaskDO]:
        po_tasks = (
            db.session.query(models.AbcXyzTask)
            .filter(models.AbcXyzTask.is_active == true())
            .filter(models.AbcXyzTask.owner_id == owner_id)
            .all()
        )
        do_tasks = [NmTaskSchemaConvert.task_po_2_do(t) for t in po_tasks]
        return do_tasks

    def get_task_by_name_type(
        self, owner_id: int, name: str, task_type: AbcXyz_TYPE
    ) -> Optional[NmTaskDO]:
        po_task = (
            db.session.query(models.AbcXyzTask)
            .filter(models.AbcXyzTask.owner_id == owner_id)
            .filter(models.AbcXyzTask.is_active == true())
            .filter(models.AbcXyzTask.name == name)
            .filter(models.AbcXyzTask.type == task_type)
            .first()
        )
        if not po_task:
            return None

        do_task = NmTaskSchemaConvert.task_po_2_do(po_task)
        return do_task

    def deactivate_task(self, abcxyz_id: int) -> None:
        db.session.query(models.AbcXyzTask).filter(
            models.AbcXyzTask.id == abcxyz_id
        ).update({"is_active": False})
        db.session.commit()

    def delete_task(self, abcxyz_id: int) -> None:
        obj = (
            db.session.query(models.AbcXyzTask)
            .filter(models.AbcXyzTask.id == abcxyz_id)
            .first()
        )

        if obj is None:
            logger.error(
                f"Task__Task_ID_NOT_EXIST: Task CRUD delete error: task id {abcxyz_id} does not exist! task_id [{abcxyz_id}]"
            )
            raise EXCEPTION_LIB.Task__Task_ID_NOT_EXIST.value(
                "Task delete error: the input task id does not exist! Please make sure your select the correct task, or input the correct id in the RESTFUL API call"
            )

        db.session.delete(obj)
        db.session.commit()

        return None

    def update_task(self, abcxyz_id: int, nm_task: NmTaskDO) -> None:
        db.session.query(models.AbcXyzTask).filter(
            models.AbcXyzTask.id == abcxyz_id
        ).update(
            {
                "ext_info": nm_task.ext_info.json(),
                "updated_at": nm_task.updated_at,
                "started_at": nm_task.started_at,
                "finished_at": nm_task.finished_at,
            }
        )

        db.session.commit()

        return None

    def get_owner_id_by_task_id(self, abcxyz_id: int) -> Optional[int]:
        do_nm_task = self.get_task(abcxyz_id=abcxyz_id)
        if not do_nm_task:
            return None

        dto_nm_task = NmTaskSchemaConvert.task_do_2_dto(do_nm_task)  # type: ignore
        owner_id = dto_nm_task.owner_id

        return owner_id

    def add_task_run_record(
        self, user_id: int, abcxyz_id: int, pod_name: str
    ) -> None:
        po_task_run_history = models.AbcXyzTaskRunHistory(
            owner_id=user_id,
            task_id=abcxyz_id,
            pod_name=pod_name,
            pod_status=POD_STATUS.RUNNING,
            started_at=datetime.datetime.utcnow(),
            finished_at=None,
            ext_info="",
        )

        try:
            db.session.add(po_task_run_history)
            db.session.commit()
        except exc.IntegrityError:
            # the owner_id is a foreign key of users table
            # owner_id must be a valid user id which exists in user table
            # otherwise, an IntegrityError is raise
            db.session.rollback()
            logger.error(
                f"TASK__DB_RECORD_INTEGRATY_ERR: owner_id [{user_id}] task_id [{abcxyz_id}] not in user or task table"
            )
            raise EXCEPTION_LIB.TASK__DB_RECORD_INTEGRATY_ERR.value(
                "The current login user is not in users table, or your task id is not in task table. Please logout and retry"
            )

        db.session.refresh(po_task_run_history)

        if po_task_run_history is None:
            logger.error(
                f"TASK__CREATE_FAILED: Create Task run history in database failed! owner_id [{user_id}] abcxyz_id[{abcxyz_id}] pod_name[{pod_name}]"
            )
            raise EXCEPTION_LIB.TASK__CREATE_FAILED.value(
                "Create task run history in database failed. Please contact the administrator"
            )

        return

    def update_task_run_record_by_id(
        self,
        run_id: int,
        pod_status: POD_STATUS,
        finished_at: datetime.datetime,
    ) -> None:
        db.session.query(models.AbcXyzTaskRunHistory).filter(
            models.AbcXyzTaskRunHistory.id == run_id
        ).update({"pod_status": pod_status, "finished_at": finished_at})
        db.session.commit()
        return

    def update_task_run_record(
        self,
        user_id: int,
        task_id: int,
        pod_name: str,
        pod_status: POD_STATUS,
        finished_at: datetime.datetime,
    ) -> None:
        db.session.query(models.AbcXyzTaskRunHistory).filter(
            models.AbcXyzTaskRunHistory.owner_id == user_id,
            models.AbcXyzTaskRunHistory.task_id == task_id,
            models.AbcXyzTaskRunHistory.pod_name == pod_name,
        ).update({"pod_status": pod_status, "finished_at": finished_at})
        db.session.commit()
        return

    def get_all_running_task_pod(self) -> List[models.AbcXyzTaskRunHistory]:
        running_task_l = (
            db.session.query(models.AbcXyzTaskRunHistory)
            .filter(
                models.AbcXyzTaskRunHistory.pod_status
                == POD_STATUS.RUNNING.value
            )
            .all()
        )
        return running_task_l

    def get_task_run_history_list(
        self, user_id: int, abcxyz_id: int
    ) -> List[models.AbcXyzTaskRunHistory]:
        run_history_l = (
            db.session.query(models.AbcXyzTaskRunHistory)
            .filter(models.AbcXyzTaskRunHistory.owner_id == user_id)
            .filter(models.AbcXyzTaskRunHistory.task_id == abcxyz_id)
            .all()
        )
        return run_history_l

    def get_records_by_started_at(
        self, user_id: int, oldest_started_at: datetime.datetime
    ) -> List[models.AbcXyzTaskRunHistory]:
        run_history_l = (
            db.session.query(models.AbcXyzTaskRunHistory)
            .filter(models.AbcXyzTaskRunHistory.owner_id == user_id)
            .filter(models.AbcXyzTaskRunHistory.started_at >= oldest_started_at)
            .all()
        )
        return run_history_l

    def delete_task_by_owner(self, owner_id: int) -> None:
        db.session.query(models.AbcXyzTask).filter(
            models.AbcXyzTask.owner_id == owner_id
        ).update({"is_active": False})
        db.session.commit()


NM_TASK_CRUD = NmTaskCrudAbsFactory.make_concrete()
