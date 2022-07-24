import datetime
from abc import ABC, abstractmethod
from typing import List, Optional

from sqlalchemy import true

from server.apps.dataset import models, schemas
from server.core.exception import EXCEPTION_LIB
from server.libs.db.sqlalchemy import db
from server.settings.global_sys_config import GLOBAL_CONFIG
from server.settings.logger import app_dataset_logger as logger


class DatasetConvert(object):
    @staticmethod
    def dataset_po_to_do(po_dataset: models.Dataset) -> schemas.DatasetDO:
        do_dataset = schemas.DatasetDO(
            id=po_dataset.id,
            name=po_dataset.name,
            description=po_dataset.description,
            owner_id=po_dataset.owner_id,
            media_id=po_dataset.media_id,
            is_active=po_dataset.is_active,
            created_at=po_dataset.created_at,
            updated_at=po_dataset.updated_at,
        )
        return do_dataset

    @staticmethod
    def dataset_do_to_dto(do_dataset: schemas.DatasetDO) -> schemas.DatasetDTO:
        return schemas.DatasetDTO(
            id=do_dataset.id,
            name=do_dataset.name,
            owner_id=do_dataset.owner_id,
            description=do_dataset.description,
            media_id=do_dataset.media_id,
            created_at=do_dataset.created_at,
            updated_at=do_dataset.updated_at,
        )


class DatasetAbsFactory(ABC, DatasetConvert):
    @abstractmethod
    def get_dataset(self, dataset_id: int) -> Optional[schemas.DatasetDO]:
        pass

    @abstractmethod
    def get_datasets_by_owner(self, owner_id: int) -> List[schemas.DatasetDO]:
        pass

    @abstractmethod
    def get_dataset_by_name(
        self, owner_id: int, name: str
    ) -> Optional[schemas.DatasetDO]:
        pass

    @abstractmethod
    def create_dataset(
        self, dataset: schemas.DatasetCreateDO
    ) -> schemas.DatasetDO:
        pass

    @abstractmethod
    def update_dataset(
        self, dataset_id: int, dataset_update: schemas.DatasetUpdateDO
    ) -> schemas.DatasetDO:
        pass

    @abstractmethod
    def delete_dataset(self, dataset_id: int) -> None:
        pass

    @abstractmethod
    def share_dataset_with_groups(
        self, dataset_id: int, group_ids: List[int]
    ) -> None:
        pass

    @abstractmethod
    def share_dataset_with_users(
        self, dataset_id: int, user_ids: List[int]
    ) -> None:
        pass

    @abstractmethod
    def get_shared_groups(self, dataset_id: int) -> List[int]:
        pass

    @abstractmethod
    def get_shared_users(self, dataset_id: int) -> List[int]:
        pass

    @abstractmethod
    def remove_shared_groups(
        self, dataset_id: int, group_ids: List[int]
    ) -> None:
        pass

    @abstractmethod
    def remove_shared_users(self, dataset_id: int, user_ids: List[int]) -> None:
        pass

    @abstractmethod
    def get_dataset_shared_with_groups(self, group_ids: List[int]) -> List[int]:
        pass

    @abstractmethod
    def get_dataset_shared_with_user(self, user_id: int) -> List[int]:
        pass

    @abstractmethod
    def get_dataset_by_ids(
        self, dataset_ids: List[int]
    ) -> List[schemas.DatasetDO]:
        pass

    @abstractmethod
    def delete_dataset_by_owner(self, owner_id: int) -> None:
        pass

    @abstractmethod
    def create_public_dataset(
        self, dataset: schemas.PublicDatasetCreateDO
    ) -> None:
        pass

    @abstractmethod
    def get_public_datasets(self) -> List[int]:
        pass

    @abstractmethod
    def delete_public_dataset(self, dataset_id: int) -> None:
        pass

    @abstractmethod
    def delete_public_dataset_by_ids(self, dataset_ids: List[int]) -> None:
        pass

    @classmethod
    def make_concrete(cls) -> "DatasetAbsFactory":
        """The factory method to load name matching metadata factory"""

        DATASET_FACTORY_DICT = {"pg": PGDatasetCRUD}

        return DATASET_FACTORY_DICT[GLOBAL_CONFIG.api_store]()


class PGDatasetCRUD(DatasetAbsFactory):
    """Dataset factory: PG Database system

    :param DatasetAbsFactory: abstract class, define the factory interface
    """

    def get_dataset(self, dataset_id: int) -> Optional[schemas.DatasetDO]:
        po_dataset = (
            db.session.query(models.Dataset)
            .filter(models.Dataset.id == dataset_id)
            .first()
        )
        if not po_dataset:
            return None

        do_dataset = self.dataset_po_to_do(po_dataset)
        return do_dataset

    def get_datasets_by_owner(self, owner_id: int) -> List[schemas.DatasetDO]:
        po_datasets = (
            db.session.query(models.Dataset)
            .filter(models.Dataset.is_active == true())
            .filter(models.Dataset.owner_id == owner_id)
            .all()
        )
        do_datasets = [self.dataset_po_to_do(d) for d in po_datasets]
        return do_datasets

    def get_dataset_by_name(
        self, owner_id: int, name: str
    ) -> Optional[schemas.DatasetDO]:
        po_dataset = (
            db.session.query(models.Dataset)
            .filter(models.Dataset.owner_id == owner_id)
            .filter(models.Dataset.name == name)
            .filter(models.Dataset.is_active == true())
            .first()
        )
        if not po_dataset:
            return None

        do_dataset = self.dataset_po_to_do(po_dataset)
        return do_dataset

    def create_dataset(
        self, dataset: schemas.DatasetCreateDO
    ) -> schemas.DatasetDO:
        po_dataset = models.Dataset(
            name=dataset.name,
            description=dataset.description,
            media_id=dataset.media_id,
            owner_id=dataset.owner_id,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        db.session.add(po_dataset)
        db.session.commit()
        db.session.refresh(po_dataset)
        if po_dataset is None:
            logger.error(f"DATASET__CREATE_FAILED: dataset [{dataset.dict()}]")
            raise EXCEPTION_LIB.DATASET__CREATE_FAILED.value(
                "Dataset create failed"
            )

        return self.dataset_po_to_do(po_dataset)

    def update_dataset(
        self, dataset_id: int, dataset_update: schemas.DatasetUpdateDO
    ) -> schemas.DatasetDO:
        db.session.query(models.Dataset).filter(
            models.Dataset.id == dataset_id
        ).update(dataset_update.dict(exclude_none=True))
        db.session.commit()

        do_dataset = self.get_dataset(dataset_id)
        if do_dataset is None:
            logger.error(
                f"DATASET__UPDATE_FAILED: dataset_update [{dataset_update.dict()}]"
            )
            raise EXCEPTION_LIB.DATASET__UPDATE_FAILED.value(
                "Dataset update failed"
            )
        return do_dataset

    def delete_dataset(self, dataset_id: int) -> None:
        db.session.query(models.Dataset).filter(
            models.Dataset.id == dataset_id
        ).delete()
        db.session.commit()

    def share_dataset_with_groups(
        self, dataset_id: int, group_ids: List[int]
    ) -> None:
        objs = []
        for gid in group_ids:
            obj = models.DatasetShareGroup(
                dataset_id=dataset_id,
                group_id=gid,
            )
            objs.append(obj)
        db.session.bulk_save_objects(objs)
        db.session.commit()

    def share_dataset_with_users(
        self, dataset_id: int, user_ids: List[int]
    ) -> None:
        objs = []
        for uid in user_ids:
            obj = models.DatasetShareUser(
                dataset_id=dataset_id,
                user_id=uid,
            )
            objs.append(obj)
        db.session.bulk_save_objects(objs)
        db.session.commit()

    def get_shared_groups(self, dataset_id: int) -> List[int]:
        groups = (
            db.session.query(models.DatasetShareGroup.group_id)
            .filter(models.DatasetShareGroup.dataset_id == dataset_id)
            .all()
        )
        return [g[0] for g in groups]

    def get_shared_users(self, dataset_id: int) -> List[int]:
        users = (
            db.session.query(models.DatasetShareUser.user_id)
            .filter(models.DatasetShareUser.dataset_id == dataset_id)
            .all()
        )

        return [u[0] for u in users]

    def remove_shared_groups(
        self, dataset_id: int, group_ids: List[int]
    ) -> None:
        db.session.query(models.DatasetShareGroup.group_id).filter(
            models.DatasetShareGroup.dataset_id == dataset_id
        ).filter(models.DatasetShareGroup.group_id.in_(group_ids)).delete(
            synchronize_session=False
        )

    def remove_shared_users(self, dataset_id: int, user_ids: List[int]) -> None:
        db.session.query(models.DatasetShareUser).filter(
            models.DatasetShareUser.dataset_id == dataset_id
        ).filter(models.DatasetShareUser.user_id.in_(user_ids)).delete(
            synchronize_session=False
        )

    def get_dataset_shared_with_groups(self, group_ids: List[int]) -> List[int]:
        if not group_ids:
            return []

        datasets = (
            db.session.query(models.DatasetShareGroup.dataset_id)
            .filter(models.DatasetShareGroup.group_id.in_(group_ids))
            .all()
        )
        return [d[0] for d in datasets]

    def get_dataset_shared_with_user(self, user_id: int) -> List[int]:
        datasets = (
            db.session.query(models.DatasetShareUser.dataset_id)
            .filter(models.DatasetShareUser.user_id == user_id)
            .all()
        )
        return [d[0] for d in datasets]

    def get_dataset_by_ids(
        self, dataset_ids: List[int]
    ) -> List[schemas.DatasetDO]:
        objs = (
            db.session.query(models.Dataset)
            .filter(models.Dataset.id.in_(dataset_ids))
            .order_by(models.Dataset.created_at.desc())
            .all()
        )

        do_datasets = [self.dataset_po_to_do(d) for d in objs]
        return do_datasets

    def delete_dataset_by_owner(self, owner_id: int) -> None:
        db.session.query(models.Dataset).filter(
            models.Dataset.owner_id == owner_id
        ).update({"is_active": False})
        db.session.commit()

    def create_public_dataset(
        self, dataset: schemas.PublicDatasetCreateDO
    ) -> None:
        po_public_dataset = models.PublicDataset(
            dataset_id=dataset.dataset_id,
            created_at=datetime.datetime.utcnow(),
        )
        db.session.add(po_public_dataset)
        db.session.commit()

        return None

    def get_public_datasets(self) -> List[int]:
        datasets = db.session.query(models.PublicDataset.dataset_id).all()
        return [d[0] for d in datasets]

    def delete_public_dataset(self, dataset_id: int) -> None:
        db.session.query(models.PublicDataset).filter(
            models.PublicDataset.dataset_id == dataset_id
        ).delete()
        db.session.commit()

    def delete_public_dataset_by_ids(self, dataset_ids: List[int]) -> None:
        db.session.query(models.PublicDataset).filter(
            models.PublicDataset.dataset_id.in_(dataset_ids)
        ).delete(synchronize_session=False)
        db.session.commit()


DATASET_CRUD = DatasetAbsFactory.make_concrete()
