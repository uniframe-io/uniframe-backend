import datetime
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import exc, true

from server.apps.group import models, schemas
from server.apps.group.schema_converter import GroupSchemaConvert
from server.core.exception import EXCEPTION_LIB
from server.libs.db.sqlalchemy import db
from server.settings.global_sys_config import GLOBAL_CONFIG


class GroupAbsFactory(ABC):
    @abstractmethod
    def get_group(self, group_id: int) -> Optional[schemas.GroupDO]:
        pass

    @abstractmethod
    def get_all_groups_owned_by_user(
        self, user_id: int
    ) -> List[schemas.GroupDO]:
        pass

    @abstractmethod
    def get_all_group_viewable_by_user(
        self, user_id: int
    ) -> List[schemas.GroupDO]:
        pass

    # @abstractmethod
    # def get_all_group_ids_viewable_by_user(self, user_id: int) -> List[int]:
    #     pass

    @abstractmethod
    def create_group(
        self, group_create: schemas.GroupCreateDO, user_id: int
    ) -> schemas.GroupDO:
        pass

    @abstractmethod
    def update_group(
        self, group_id: int, group_update: schemas.GroupUpdateDO
    ) -> schemas.GroupDO:
        pass

    @abstractmethod
    def delete_group(self, group_id: int) -> None:
        pass

    @abstractmethod
    def add_group_member(self, group_id: int, member_id: int) -> None:
        pass

    @abstractmethod
    def delete_group_member(self, group_id: int, member_id: int) -> None:
        pass

    @abstractmethod
    def get_group_members(self, group_id: int) -> schemas.GroupMembersDO:
        pass

    @abstractmethod
    def update_group_members(
        self, group_id: int, add_members: List[int], delete_members: List[int]
    ) -> schemas.GroupMembersDO:
        pass

    @abstractmethod
    def get_group_by_ids(self, group_ids: List[int]) -> List[schemas.GroupDO]:
        pass

    @classmethod
    def make_concrete(cls) -> "GroupAbsFactory":
        """The factory method to load name matching metadata factory"""

        GROUP_FACTORY_DICT = {"pg": PGGroupCRUD}

        return GROUP_FACTORY_DICT[GLOBAL_CONFIG.api_store]()


class PGGroupCRUD(GroupAbsFactory):
    """User factory: PG Database system

    :param UserAbsFactory: abstract class, define the factory interface
    """

    def get_group(self, group_id: int) -> Optional[schemas.GroupDO]:
        po_group = (
            db.session.query(models.Group)
            .filter(models.Group.id == group_id)
            .first()
        )

        if not po_group:
            return None

        do_group = GroupSchemaConvert.group_po_2_do(po_group)
        return do_group

    def get_all_groups_owned_by_user(
        self, user_id: int
    ) -> List[schemas.GroupDO]:
        po_groups = (
            db.session.query(models.Group)
            .filter(models.Group.owner_id == user_id)
            .filter(models.Group.is_active == true())
            .all()
        )

        if not po_groups:
            return []

        do_groups = [GroupSchemaConvert.group_po_2_do(g) for g in po_groups]
        return do_groups

    def get_all_group_viewable_by_user(
        self, user_id: int
    ) -> List[schemas.GroupDO]:
        group_member_ids = db.session.query(
            models.GroupMembers.group_id
        ).filter(models.GroupMembers.member_id == user_id)
        po_groups = (
            db.session.query(models.Group)
            .filter(models.Group.id.in_(group_member_ids))
            .all()
        )

        if not po_groups:
            return []

        do_groups = [GroupSchemaConvert.group_po_2_do(g) for g in po_groups]
        return do_groups

    def create_group(
        self, group_create: schemas.GroupCreateDO, user_id: int
    ) -> schemas.GroupDO:
        po_group = models.Group(
            owner_id=user_id,
            name=group_create.name,
            description=group_create.description,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            ext_info="",
        )
        try:
            db.session.add(po_group)
            db.session.commit()
        except exc.IntegrityError:
            # the owner_id is a foreign key of users table
            # owner_id must be a valid user id which exists in user table
            # otherwise, an IntegrityError is raise
            db.session.rollback()
            raise EXCEPTION_LIB.GROUP__GROUP_OWNER_ID_NOT_IN_USER_TABLE.value(
                f"The group owner id {user_id} not in users table"
            )

        db.session.refresh(po_group)

        if po_group is None:
            raise EXCEPTION_LIB.GROUP__CREATE_FAILED.value(
                "Create Group in database failed"
            )

        return GroupSchemaConvert.group_po_2_do(po_group)

    def update_group(
        self, group_id: int, group_update: schemas.GroupUpdateDO
    ) -> schemas.GroupDO:
        # if group_id doesn't exist, the update will still return successfully
        (
            db.session.query(models.Group)
            .filter(models.Group.id == group_id)
            .update(
                {
                    "name": group_update.name,
                    "description": group_update.description,
                    "updated_at": datetime.datetime.utcnow(),
                }
            )
        )
        db.session.commit()

        do_group = self.get_group(group_id)
        if do_group is None:
            raise EXCEPTION_LIB.GROUP__GROUP_ID_NOT_EXIST.value(
                f"Group {group_id} update failed"
            )
        return do_group

    def delete_group(self, group_id: int) -> None:
        """
        delete a group record by given group id
        """
        try:
            obj = (
                db.session.query(models.Group)
                .filter(models.Group.id == group_id)
                .first()
            )

            if obj is None:
                raise EXCEPTION_LIB.GROUP__GROUP_ID_NOT_EXIST.value(
                    f"Group CRUD delete error: group id {group_id} does not exist!"
                )

            db.session.delete(obj)
            db.session.commit()
        except exc.IntegrityError:
            # the group_id is a foreign key of group_members, and other table in future
            # we need to release all relationship of group-member or group-tasks before we delete the group
            db.session.rollback()
            raise EXCEPTION_LIB.GROUP__GROUP_STILL_USED_BY_OTHER_TABLES.value(
                f"Delete group failed: the group {group_id} is still used by other tables"
            )

        return None

    def add_group_member(self, group_id: int, member_id: int) -> None:
        """
        Must does authorization checking before calling this function
        """
        po_group_member = models.GroupMembers(
            group_id=group_id, member_id=member_id
        )

        try:
            db.session.add(po_group_member)
            db.session.commit()
        except exc.IntegrityError:
            # the group id and user id are foreign keys of users and group table
            # group id and user id must be a valid id which exist in tables
            # otherwise, an IntegrityError is raise
            db.session.rollback()
            raise EXCEPTION_LIB.GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_INTEGRITY_ERROR.value(
                f"Either group id {group_id} or user id {member_id} not exist! {exc.IntegrityError}"
            )

        return None

    def delete_group_member(self, group_id: int, member_id: int) -> None:
        """
        Must does authorization checking before calling this function
        """
        obj = (
            db.session.query(models.GroupMembers)
            .filter(models.GroupMembers.group_id == group_id)
            .filter(models.GroupMembers.member_id == member_id)
            .first()
        )
        if obj is None:
            raise EXCEPTION_LIB.GROUP__GROUP_MEMBERS_USER_ID_OR_GROUP_ID_NOT_EXIST.value(
                f"Group CRUD delete_group_member error:  group_id = {group_id} and user_id = {member_id} does not exist!"
            )

        db.session.delete(obj)
        db.session.commit()

        return None

    def get_group_members(self, group_id: int) -> schemas.GroupMembersDO:
        """
        Must does authorization checking before calling this function
        """
        po_group_members = (
            db.session.query(models.GroupMembers)
            .filter(models.GroupMembers.group_id == group_id)
            .all()
        )

        if not po_group_members:
            return schemas.GroupMembersDO(group_id=group_id, members=list())

        do_group_members = GroupSchemaConvert.group_members_po_2_do(
            group_id, po_group_members
        )

        return do_group_members

    def update_group_members(
        self, group_id: int, add_members: List[int], delete_members: List[int]
    ) -> schemas.GroupMembersDO:
        """
        update group members in one transaction
        - add_members: the member to be added
        - delete_members: the member to be deleted
        """
        # bulk delete
        if delete_members:
            (
                db.session.query(models.GroupMembers)
                .filter(models.GroupMembers.member_id.in_(delete_members))
                .filter(models.GroupMembers.group_id == group_id)
                .delete(synchronize_session="fetch")
            )
        # bulk insert
        if add_members:
            add_objs = [
                models.GroupMembers(group_id=group_id, member_id=member_id)
                for member_id in add_members
            ]
            db.session.bulk_save_objects(add_objs)

        db.session.commit()

        return self.get_group_members(group_id)

    def get_group_by_ids(self, group_ids: List[int]) -> List[schemas.GroupDO]:
        groups = (
            db.session.query(models.Group)
            .filter(models.Group.id.in_(group_ids))
            .all()
        )

        do_groups = [GroupSchemaConvert.group_po_2_do(g) for g in groups]
        return do_groups


GROUP_CRUD = GroupAbsFactory.make_concrete()
