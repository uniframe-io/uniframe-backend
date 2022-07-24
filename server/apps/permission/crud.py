import datetime
from abc import ABC, abstractmethod
from typing import Optional

from server.apps.permission import models, schemas
from server.core.exception import EXCEPTION_LIB
from server.libs.db.sqlalchemy import db
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_permission_logger as logger


class LocalDeployUserConvert(object):
    @staticmethod
    def local_deploy_user_po_to_do(
        po_local_deploy_user: models.LocalDeployUser,
    ) -> schemas.LocalDeployUserDO:
        do_local_deploy_user = schemas.LocalDeployUserDO(
            id=po_local_deploy_user.id,
            email=po_local_deploy_user.email,
            user_id=po_local_deploy_user.user_id,
            is_active=po_local_deploy_user.is_active,
            company=po_local_deploy_user.company,
            role=po_local_deploy_user.role,
            purpose=po_local_deploy_user.purpose,
            requested_at=po_local_deploy_user.requested_at,
            approved_at=po_local_deploy_user.approved_at,
            expire_at=po_local_deploy_user.expire_at,
        )
        return do_local_deploy_user


class LocalDeployUserAbsFactory(ABC, LocalDeployUserConvert):
    @abstractmethod
    def get_local_deploy_user(
        self, user_id: int
    ) -> Optional[schemas.LocalDeployUserDO]:
        pass

    @abstractmethod
    def create_local_deploy_user(
        self, local_deploy_user: schemas.LocalDeployUserCreateDO
    ) -> schemas.LocalDeployUserDO:
        pass

    @abstractmethod
    def update_local_deploy_user(
        self, new_local_deploy_user: schemas.LocalDeployUserDO
    ) -> schemas.LocalDeployUserDO:
        pass

    @abstractmethod
    def delete_local_deploy_user(self, local_user_id: int) -> None:
        pass

    @classmethod
    def make_concrete(cls) -> "LocalDeployUserAbsFactory":
        """The factory method to load name matching metadata factory"""

        DATASET_FACTORY_DICT = {"pg": PGLocalDeployUserCRUD}

        return DATASET_FACTORY_DICT[GLOBAL_CONFIG.api_store]()


class PGLocalDeployUserCRUD(LocalDeployUserAbsFactory):
    """Oauth factory: PG Database system

    :param OauthAbsFactory: abstract class, define the factory interface
    """

    def get_local_deploy_user(
        self, user_id: int
    ) -> Optional[schemas.LocalDeployUserDO]:
        po_local_deploy_user = (
            db.session.query(models.LocalDeployUser)
            .filter(models.LocalDeployUser.user_id == user_id)
            .first()
        )
        if not po_local_deploy_user:
            return None

        do_local_deploy_user = self.local_deploy_user_po_to_do(
            po_local_deploy_user
        )
        return do_local_deploy_user

    def create_local_deploy_user(
        self, local_deploy_user: schemas.LocalDeployUserCreateDO
    ) -> schemas.LocalDeployUserDO:
        po_local_deploy_user = models.LocalDeployUser(
            email=local_deploy_user.email,
            user_id=local_deploy_user.user_id,
            is_active=False,
            company=local_deploy_user.company,
            role=local_deploy_user.role,
            purpose=local_deploy_user.purpose,
            requested_at=datetime.datetime.utcnow(),
            approved_at=None,
            expire_at=None,
        )
        db.session.add(po_local_deploy_user)
        db.session.commit()
        db.session.refresh(po_local_deploy_user)

        if po_local_deploy_user is None:
            logger.error(
                f"LOCAL_DEPLOY__CREATE_FAILED: local_deploy_user [{local_deploy_user.user_id}]"
            )
            raise EXCEPTION_LIB.LOCAL_DEPLOY__CREATE_FAILED.value(
                "Create local deployment request in database failed"
            )

        return self.local_deploy_user_po_to_do(po_local_deploy_user)

    def update_local_deploy_user(
        self, local_deploy_user_update: schemas.LocalDeployUserDO
    ) -> schemas.LocalDeployUserDO:
        user_id = local_deploy_user_update.user_id

        db.session.query(models.LocalDeployUser).filter(
            models.LocalDeployUser.user_id == user_id
        ).update(local_deploy_user_update.dict(exclude_none=True))
        db.session.commit()

        do_local_deploy_user = self.get_local_deploy_user(user_id)
        if do_local_deploy_user is None:
            logger.error(
                f"LOCAL_DEPLOY__UPDATE_FAILED: local_deploy_user_update [{local_deploy_user_update.dict()}]"
            )
            raise EXCEPTION_LIB.LOCAL_DEPLOY__UPDATE_FAILED.value(
                "Create local deployment request in database failed"
            )
        return do_local_deploy_user

    def delete_local_deploy_user(self, local_user_id: int) -> None:
        (
            db.session.query(models.LocalDeployUser)
            .filter(models.LocalDeployUser.id == local_user_id)
            .delete()
        )
        db.session.commit()


LOCAL_DEPLOY_USER_CRUD = LocalDeployUserAbsFactory.make_concrete()
