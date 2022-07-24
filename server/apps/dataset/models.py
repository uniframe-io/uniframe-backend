from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from server.libs.db.sqlalchemy import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200))
    description = Column(String(200))
    media_id = Column(Integer, ForeignKey("medias.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)


class DatasetShareUser(Base):
    __tablename__ = "dataset_shared_users"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    user_id = Column(Integer, ForeignKey("users.id"))


class DatasetShareGroup(Base):
    __tablename__ = "dataset_shared_groups"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))


class PublicDataset(Base):
    __tablename__ = "public_datasets"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    dataset_id = Column(Integer, ForeignKey("datasets.id"), unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
