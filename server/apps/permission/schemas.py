import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class LocalDeployUserBase(BaseModel):
    company: str
    role: str
    purpose: str


class LocalDeployUserCreateDTO(LocalDeployUserBase):
    pass


class LocalDeployUserCreateDO(LocalDeployUserBase):
    email: EmailStr
    user_id: int


class LocalDeployUserDO(LocalDeployUserBase):
    id: int
    email: EmailStr
    user_id: int
    is_active: bool
    requested_at: datetime.datetime
    approved_at: Optional[datetime.datetime]
    expire_at: Optional[datetime.datetime]


class LocalDeployUserDTO(LocalDeployUserBase):
    id: int
    requested_at: datetime.datetime
    approved_at: Optional[datetime.datetime]
    expire_at: Optional[datetime.datetime]


class AwsSessionToken(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str
