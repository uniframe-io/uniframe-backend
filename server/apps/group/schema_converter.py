from typing import List

from server.apps.group import models, schemas


class GroupSchemaConvert(object):
    @staticmethod
    def group_po_2_do(po: models.Group) -> schemas.GroupDO:
        do = schemas.GroupDO(
            id=po.id,
            name=po.name,
            description=po.description,
            owner_id=po.owner_id,
            is_active=po.is_active,
            created_at=po.created_at,
            updated_at=po.updated_at,
        )
        return do

    @staticmethod
    def group_do_2_dto(do: schemas.GroupDO) -> schemas.GroupDTO:
        return schemas.GroupDTO(**do.dict())

    @staticmethod
    def group_create_dto_2_do(
        dto_create: schemas.GroupCreateDTO,
    ) -> schemas.GroupCreateDO:
        return schemas.GroupCreateDO(**dto_create.dict())

    @staticmethod
    def group_update_dto_2_do(
        dto_update: schemas.GroupUpdateDTO,
    ) -> schemas.GroupUpdateDO:
        return schemas.GroupUpdateDO(**dto_update.dict())

    @staticmethod
    def group_members_po_2_do(
        group_id: int, po: List[models.GroupMembers]
    ) -> schemas.GroupMembersDO:
        do = schemas.GroupMembersDO(
            group_id=group_id,
            members=[group_member.member_id for group_member in po],
        )
        return do

    @staticmethod
    def group_members_do_2_dto(
        do: schemas.GroupMembersDO,
    ) -> schemas.GroupMembersDTO:
        return schemas.GroupMembersDTO(**do.dict())
