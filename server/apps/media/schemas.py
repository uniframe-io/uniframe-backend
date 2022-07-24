import datetime
import enum
from typing import List

from pydantic import BaseModel


class MEDIA_CONTENT_TYPE(str, enum.Enum):
    CSV = "text/csv"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    XLS = "application/vnd.ms-excel"

    @staticmethod
    def list() -> List:
        return list(map(lambda c: c.value, MEDIA_CONTENT_TYPE))


class MediaExtInfo(BaseModel):
    header: List[str]
    first_n_rows: str
    file_name: str
    media_type: MEDIA_CONTENT_TYPE


class MediaBase(BaseModel):
    ext_info: MediaExtInfo


class MediaDTO(MediaBase):
    id: int
    owner_id: int
    e_tag: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class MediaDO(MediaBase):
    id: int
    owner_id: int
    e_tag: str
    location: str
    is_active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime


class MediaUpdateDO(BaseModel):
    is_active: bool


class MediaCreateDO(MediaBase):
    location: str
    owner_id: int
    e_tag: str
