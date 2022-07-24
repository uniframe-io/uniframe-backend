import datetime
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional

from sqlalchemy import true

from server.apps.oauth import models, schemas
from server.apps.user.models import User
from server.core.exception import EXCEPTION_LIB
from server.libs.db.sqlalchemy import db
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_oauth_logger as logger


class OAuthConvert(object):
    @staticmethod
    def oauth2_user_po_to_do(
        po_oauth2: models.OAuth2User,
    ) -> schemas.OAuth2UserDo:
        do_oauth2 = schemas.OAuth2UserDo(
            id=po_oauth2.id,
            provider=po_oauth2.provider,
            provider_id=po_oauth2.provider_id,
            owner_id=po_oauth2.owner_id,
            ext_info=po_oauth2.ext_info,
            is_active=po_oauth2.is_active,
            created_at=po_oauth2.created_at,
            updated_at=po_oauth2.updated_at,
        )
        return do_oauth2

    @staticmethod
    def verification_code_po_to_do(
        po_vcode: models.VerificationCode,
    ) -> schemas.VerificationCodeDO:
        do_vcode = schemas.VerificationCodeDO(
            id=po_vcode.id,
            email=po_vcode.email,
            action=po_vcode.action,
            vcode=po_vcode.vcode,
            is_active=po_vcode.is_active,
            expire_at=po_vcode.expire_at,
            created_at=po_vcode.created_at,
            updated_at=po_vcode.updated_at,
        )
        return do_vcode


class OauthAbsFactory(ABC, OAuthConvert):
    @abstractmethod
    def get_oauth2_user(
        self, provider: str, provider_id: int
    ) -> Optional[schemas.OAuth2UserDo]:
        pass

    @abstractmethod
    def create_oauth2_user(
        self, dataset: schemas.OAuth2UserCreateDO
    ) -> schemas.OAuth2UserDo:
        pass

    @abstractmethod
    def update_oauth2_user(
        self, owner_id: int, oauth2_user: schemas.OAuth2UserUpdateDO
    ) -> None:
        pass

    @abstractmethod
    def delete_oauth2_user(self, oauth2_id: int) -> None:
        pass

    @abstractmethod
    def get_vcode(
        self, action: str, email: str
    ) -> Optional[schemas.VerificationCodeDO]:
        pass

    @abstractmethod
    def get_vcode_count(self, action: str, email: str) -> int:
        pass

    @abstractmethod
    def create_vcode(
        self, dataset: schemas.VerificationCodeCreateDO
    ) -> schemas.VerificationCodeDO:
        pass

    @abstractmethod
    def delete_vcode_by_action(self, action: str, email: str) -> None:
        pass

    @abstractmethod
    def delete_vcode(self, vid: int) -> None:
        pass

    @classmethod
    def make_concrete(cls) -> "OauthAbsFactory":
        """The factory method to load name matching metadata factory"""

        DATASET_FACTORY_DICT = {"pg": PGOauthCRUD}

        return DATASET_FACTORY_DICT[GLOBAL_CONFIG.api_store]()


class PGOauthCRUD(OauthAbsFactory):
    """Oauth factory: PG Database system

    :param OauthAbsFactory: abstract class, define the factory interface
    """

    def get_oauth2_user(
        self, provider: str, provider_id: int
    ) -> Optional[schemas.OAuth2UserDo]:
        po_oauth2 = (
            db.session.query(models.OAuth2User)
            .filter(models.OAuth2User.provider == provider)
            .filter(models.OAuth2User.provider_id == provider_id)
            .first()
        )
        if not po_oauth2:
            return None

        do_oauth2 = self.oauth2_user_po_to_do(po_oauth2)
        return do_oauth2

    def create_oauth2_user(
        self, oauth2_user: schemas.OAuth2UserCreateDO
    ) -> schemas.OAuth2UserDo:
        po_user = User(
            full_name=oauth2_user.full_name,
            email=oauth2_user.email,
            login_type=oauth2_user.login_type,
            is_active=True,
            is_superuser=False,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(po_user)
        db.session.commit()

        po_oauth2_user = models.OAuth2User(
            owner_id=po_user.id,
            provider=oauth2_user.provider,
            provider_id=oauth2_user.provider_id,
            ext_info=oauth2_user.ext_info,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(po_oauth2_user)
        db.session.commit()
        db.session.refresh(po_oauth2_user)

        if po_oauth2_user is None:
            logger.error(
                f"OAUTH2__CREATE_FAILED: oauth2_user [{oauth2_user.full_name}]"
            )
            raise EXCEPTION_LIB.OAUTH2__CREATE_FAILED.value(
                "Oauth2 user create failed"
            )

        return self.oauth2_user_po_to_do(po_oauth2_user)

    def delete_oauth2_user(self, oauth2_id: int) -> None:
        db.session.query(models.OAuth2User).filter(
            models.OAuth2User.id == oauth2_id
        ).delete()
        db.session.commit()

    def update_oauth2_user(
        self, owner_id: int, oauth2_user_update: schemas.OAuth2UserUpdateDO
    ) -> None:
        db.session.query(models.OAuth2User).filter(
            models.OAuth2User.owner_id == owner_id
        ).update(oauth2_user_update.dict(exclude_none=True))
        db.session.commit()

    def get_vcode(
        self, action: str, email: str
    ) -> Optional[schemas.VerificationCodeDO]:
        po_vcode = (
            db.session.query(models.VerificationCode)
            .filter(models.VerificationCode.email == email)
            .filter(models.VerificationCode.action == action)
            .filter(models.VerificationCode.is_active == true())
            .order_by(models.VerificationCode.created_at.desc())
            .first()
        )
        if not po_vcode:
            return None

        do_vcode = self.verification_code_po_to_do(po_vcode)
        return do_vcode

    def get_vcode_count(self, action: str, email: str) -> int:
        now = datetime.datetime.utcnow()
        one_day_ago = now - timedelta(hours=1)

        cnt = (
            db.session.query(models.VerificationCode)
            .filter(models.VerificationCode.email == email)
            .filter(models.VerificationCode.action == action)
            .filter(models.VerificationCode.created_at > one_day_ago)
            .count()
        )
        return cnt

    def create_vcode(
        self, do_vcode: schemas.VerificationCodeCreateDO
    ) -> schemas.VerificationCodeDO:
        po_vcode = models.VerificationCode(
            email=do_vcode.email,
            action=do_vcode.action,
            vcode=do_vcode.vcode,
            expire_at=do_vcode.expire_at,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(po_vcode)
        db.session.commit()
        db.session.refresh(po_vcode)

        if po_vcode is None:
            raise EXCEPTION_LIB.VCODE__CREATE_FAILED.value(
                "vcode create failed"
            )

        return self.verification_code_po_to_do(po_vcode)

    def delete_vcode_by_action(self, action: str, email: str) -> None:
        db.session.query(models.VerificationCode).filter(
            models.VerificationCode.action == action
        ).filter(models.VerificationCode.email == email).update(
            {"is_active": False}
        )
        db.session.commit()

    def delete_vcode(self, vid: int) -> None:
        db.session.query(models.VerificationCode).filter(
            models.VerificationCode.id == vid
        ).delete()
        db.session.commit()


OAUTH_CRUD = OauthAbsFactory.make_concrete()
