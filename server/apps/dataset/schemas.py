import datetime
import enum
from typing import List, Optional

from pydantic import BaseModel

from server.apps.media.schemas import MediaDTO


class OWNERSHIP_TYPE(str, enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    SHARED = "shared"


class DatasetBase(BaseModel):
    name: str
    description: str
    media_id: int


class DatasetDTO(DatasetBase):
    id: int
    owner_id: int
    media: Optional[MediaDTO]
    ownership_type: Optional[OWNERSHIP_TYPE]
    created_at: datetime.datetime
    updated_at: datetime.datetime


class DatasetDO(DatasetBase):
    id: int
    is_active: bool = True
    owner_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class DatasetCreateDTO(DatasetBase):
    pass


class DatasetCreateDO(DatasetBase):
    owner_id: int


class DatasetUpdateDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DatasetUpdateDO(DatasetUpdateDTO):
    is_active: Optional[bool] = None


class DatasetShareDTO(BaseModel):
    group_ids: Optional[List[int]]
    user_ids: Optional[List[int]]


class DatasetStatTask(BaseModel):
    id: int
    name: str
    type: str


class DatasetStatDTO(BaseModel):
    used_by_tasks: List[DatasetStatTask]


class PublicDatasetBase(BaseModel):
    dataset_id: int


class PublicDatasetCreateDO(PublicDatasetBase):
    pass
