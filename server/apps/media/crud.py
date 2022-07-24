import datetime
from abc import ABC, abstractmethod
from typing import List, Optional

from server.apps.media import models, schemas
from server.core.exception import EXCEPTION_LIB
from server.libs.db.sqlalchemy import db
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_media_logger as logger


class MediaConvert(object):
    @staticmethod
    def media_po_to_do(po_media: models.Media) -> schemas.MediaDO:
        do_media = schemas.MediaDO(
            id=po_media.id,
            owner_id=po_media.owner_id,
            location=po_media.location,
            e_tag=po_media.e_tag,
            ext_info=schemas.MediaExtInfo.parse_raw(po_media.ext_info),
            is_active=po_media.is_active,
            created_at=po_media.created_at,
            updated_at=po_media.updated_at,
        )
        return do_media

    @staticmethod
    def media_do_to_dto(do_media: schemas.MediaDO) -> schemas.MediaDTO:
        return schemas.MediaDTO(
            id=do_media.id,
            owner_id=do_media.owner_id,
            e_tag=do_media.e_tag,
            ext_info=do_media.ext_info,
            created_at=do_media.created_at,
            updated_at=do_media.updated_at,
        )


class MediaAbsFactory(ABC, MediaConvert):
    @abstractmethod
    def get_media(self, media_id: int) -> Optional[schemas.MediaDO]:
        pass

    @abstractmethod
    def get_media_by_etag(
        self, owner_id: int, etag: str
    ) -> Optional[schemas.MediaDO]:
        pass

    @abstractmethod
    def create_media(self, dataset: schemas.MediaCreateDO) -> schemas.MediaDO:
        pass

    @abstractmethod
    def delete_media(self, media_id: int) -> None:
        pass

    @abstractmethod
    def delete_media_by_owner(self, owner_id: int) -> None:
        pass

    @abstractmethod
    def get_all_medias_by_owner(self, owner_id: int) -> List[schemas.MediaDO]:
        pass

    @classmethod
    def make_concrete(cls) -> "MediaAbsFactory":
        """The factory method to load name matching metadata factory"""

        DATASET_FACTORY_DICT = {"pg": PGMediaCRUD}

        return DATASET_FACTORY_DICT[GLOBAL_CONFIG.api_store]()


class PGMediaCRUD(MediaAbsFactory):
    """Media factory: PG Database system

    :param DatasetAbsFactory: abstract class, define the factory interface
    """

    def get_media(self, media_id: int) -> Optional[schemas.MediaDO]:
        po_media = (
            db.session.query(models.Media)
            .filter(models.Media.id == media_id)
            .first()
        )
        if not po_media:
            return None

        do_media = self.media_po_to_do(po_media)
        return do_media

    def create_media(self, media: schemas.MediaCreateDO) -> schemas.MediaDO:
        po_media = models.Media(
            owner_id=media.owner_id,
            location=media.location,
            e_tag=media.e_tag,
            ext_info=media.ext_info.json(),
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(po_media)
        db.session.commit()
        db.session.refresh(po_media)
        if po_media is None:
            logger.info(f"MEDIA__CREATE_FAILED: media [{media.dict()}]")
            raise EXCEPTION_LIB.MEDIA__CREATE_FAILED.value(
                "Media create failed"
            )

        return self.media_po_to_do(po_media)

    def delete_media(self, media_id: int) -> None:
        db.session.query(models.Media).filter(
            models.Media.id == media_id
        ).delete()
        db.session.commit()

    def get_media_by_etag(
        self, owner_id: int, etag: str
    ) -> Optional[schemas.MediaDO]:
        po_media = (
            db.session.query(models.Media)
            .filter(models.Media.e_tag == etag)
            .filter(models.Media.owner_id == owner_id)
            .first()
        )
        if not po_media:
            return None

        do_media = self.media_po_to_do(po_media)
        return do_media

    def delete_media_by_owner(self, owner_id: int) -> None:
        db.session.query(models.Media).filter(
            models.Media.owner_id == owner_id
        ).update(
            {
                "is_active": False,
                "ext_info": schemas.MediaExtInfo(
                    header=["deleted"],
                    first_n_rows="deleted",
                    file_name="deleted",
                    media_type="text/csv",
                ).json(),
            }
        )
        db.session.commit()

    def get_all_medias_by_owner(self, owner_id: int) -> List[schemas.MediaDO]:
        po_medias = (
            db.session.query(models.Media)
            .filter(models.Media.owner_id == owner_id)
            .all()
        )
        do_medias = [self.media_po_to_do(m) for m in po_medias]
        return do_medias


MEDIA_CRUD = MediaAbsFactory.make_concrete()
