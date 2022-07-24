import datetime
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import true

from server.apps.user import models, schemas
from server.core.exception import EXCEPTION_LIB
from server.libs.db.sqlalchemy import db
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_user_logger as logger


class UserConvert(object):
    @staticmethod
    def user_po_to_do(po_user: models.User) -> schemas.UserDO:
        do_user = schemas.UserDO(
            id=po_user.id,
            email=po_user.email,
            is_active=po_user.is_active,
            is_superuser=po_user.is_superuser,
            login_type=po_user.login_type,
            full_name=po_user.full_name,
            hashed_password=po_user.hashed_password,
            created_at=po_user.created_at,
            updated_at=po_user.updated_at,
        )
        return do_user

    @staticmethod
    def user_do_to_dto(do_user: schemas.UserDO) -> schemas.UserDTO:
        return schemas.UserDTO(
            id=do_user.id,
            email=do_user.email,
            login_type=do_user.login_type,
            full_name=do_user.full_name,
            created_at=do_user.created_at,
        )


class UserAbsFactory(ABC, UserConvert):
    @abstractmethod
    def get_user(self, user_id: int) -> Optional[schemas.UserDO]:
        pass

    @abstractmethod
    def get_all_users(self) -> List[schemas.UserDO]:
        pass

    @abstractmethod
    def create_user(
        self, user: schemas.UserCreateDO, is_superuser: bool = False
    ) -> schemas.UserDO:
        pass

    @abstractmethod
    def update_user(
        self, user_id: int, user_update: schemas.UserUpdateDO
    ) -> schemas.UserDO:
        pass

    @abstractmethod
    def delete_user(self, user_id: int) -> None:
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[schemas.UserDO]:
        pass

    @abstractmethod
    def get_user_by_ids(self, user_ids: List[int]) -> List[schemas.UserDO]:
        pass

    @classmethod
    def make_concrete(cls) -> "UserAbsFactory":
        """The factory method to load name matching metadata factory"""

        USER_FACTORY_DICT = {"pg": PGUserCRUD}

        return USER_FACTORY_DICT[GLOBAL_CONFIG.api_store]()


class PGUserCRUD(UserAbsFactory):
    """User factory: PG Database system

    :param UserAbsFactory: abstract class, define the factory interface
    """

    def get_user(self, user_id: int) -> Optional[schemas.UserDO]:
        po_user = (
            db.session.query(models.User)
            .filter(models.User.id == user_id)
            .first()
        )
        if not po_user:
            return None

        do_user = self.user_po_to_do(po_user)
        return do_user

    def get_all_users(self) -> List[schemas.UserDO]:
        po_users = (
            db.session.query(models.User)
            .filter(models.User.is_active == true())
            .all()
        )
        do_users = [self.user_po_to_do(u) for u in po_users]
        return do_users

    def create_user(
        self, user: schemas.UserCreateDO, is_superuser: bool = False
    ) -> schemas.UserDO:
        po_user = models.User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=user.hashed_password,
            is_active=True,
            is_superuser=is_superuser,
            login_type=user.login_type,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(po_user)
        db.session.commit()
        db.session.refresh(po_user)

        if po_user is None:
            logger.error(f"USER__CREATE_FAILED: user [{user.full_name}]")
            raise EXCEPTION_LIB.USER__CREATE_FAILED.value("User create failed")

        return self.user_po_to_do(po_user)

    def update_user(
        self, user_id: int, user_update: schemas.UserUpdateDO
    ) -> schemas.UserDO:
        db.session.query(models.User).filter(models.User.id == user_id).update(
            user_update.dict(exclude_none=True)
        )
        db.session.commit()

        do_user = self.get_user(user_id)
        if do_user is None:
            logger.error(f"USER__UPDATE_FAILED: user [{user_id}]")
            raise EXCEPTION_LIB.USER__UPDATE_FAILED.value("User update failed")
        return do_user

    def delete_user(self, user_id: int) -> None:
        (
            db.session.query(models.User)
            .filter(models.User.id == user_id)
            .delete()
        )
        db.session.commit()

        return None

    def get_user_by_email(self, email: str) -> Optional[schemas.UserDO]:
        po_user = (
            db.session.query(models.User)
            .filter(models.User.email == email)
            .first()
        )
        if not po_user:
            return None
        return self.user_po_to_do(po_user)

    def get_user_by_ids(self, user_ids: List[int]) -> List[schemas.UserDO]:
        po_users = (
            db.session.query(models.User)
            .filter(models.User.id.in_(user_ids))
            .all()
        )

        do_users = [self.user_po_to_do(u) for u in po_users]
        return do_users


USER_CRUD = UserAbsFactory.make_concrete()
