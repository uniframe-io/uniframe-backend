from server.apps.nm_task import models, schemas
from server.core.exception import EXCEPTION_LIB
from server.settings.logger import app_nm_task_logger as logger


class NmTaskSchemaConvert(object):
    @staticmethod
    def task_po_2_do(
        po: models.AbcXyzTask,
    ) -> schemas.NmTaskDO:
        if po.type == schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME:
            do = schemas.NmTaskDO(
                id=po.id,
                name=po.name,
                description=po.description,
                owner_id=po.owner_id,
                is_public=po.is_public,
                is_active=po.is_active,
                type=po.type,
                created_at=po.created_at,
                updated_at=po.updated_at,
                started_at=po.started_at,
                finished_at=po.finished_at,
                ext_info=schemas.NmCfgRtSchema.parse_raw(po.ext_info),
            )
        elif po.type == schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH:
            do = schemas.NmTaskDO(
                id=po.id,
                name=po.name,
                description=po.description,
                owner_id=po.owner_id,
                is_public=po.is_public,
                is_active=po.is_active,
                type=po.type,
                created_at=po.created_at,
                updated_at=po.updated_at,
                started_at=po.started_at,
                finished_at=po.finished_at,
                ext_info=schemas.NmCfgBatchSchema.parse_raw(po.ext_info),
            )
        else:
            logger.error(
                f"TASK__TASK_TYPE_NOT_VALID: Task type is {po.type}, which is not valid! task_id [{po.id}]"
            )
            raise EXCEPTION_LIB.TASK__TASK_TYPE_NOT_VALID.value(
                f"The input task type is {po.type}, which is not valid. We only support {schemas.AbcXyz_TYPE.NAME_MATCHING_BATCH} and {schemas.AbcXyz_TYPE.NAME_MATCHING_REALTIME} type"
            )
        return do

    @staticmethod
    def task_do_2_dto(do: schemas.NmTaskDO) -> schemas.NmTaskDTO:
        dto = schemas.NmTaskDTO(**do.dict())  # type: ignore
        return dto

    @staticmethod
    def task_create_dto_2_do(
        dto: schemas.NmTaskCreateDTO,
    ) -> schemas.NmTaskCreateDO:
        do = schemas.NmTaskCreateDO(**dto.dict())
        return do
