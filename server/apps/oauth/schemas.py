import datetime
import enum
from typing import Optional

from pydantic import BaseModel, EmailStr

from server.apps.user.schemas import LOGIN_TYPE, UserDTO


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserDTO


class TokenPayload(BaseModel):
    sub: int


class OAUTH2_PROVIDER_TYPE(str, enum.Enum):
    PROVIDER_GITHUB = "github"
    PROVIDER_GOOGLE = "google"


class OAuth2Base(BaseModel):
    provider_id: int
    provider: str
    ext_info: str


class OAuth2UserCreateDO(OAuth2Base):
    full_name: str
    email: Optional[EmailStr]
    login_type: LOGIN_TYPE


class OAuth2UserDo(OAuth2Base):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


class OAuth2UserUpdateDO(BaseModel):
    is_active: bool = True
    ext_info: str


class ACTION_TYPE(str, enum.Enum):
    ACTION_FORGET_PASSWORD = "forget_password"
    ACTION_SIGNUP = "signup"


class VCodeBase(BaseModel):
    email: EmailStr
    action: ACTION_TYPE


class VCodeSendDTO(VCodeBase):
    pass


class VCodeVerifyDTO(VCodeBase):
    vcode: str


class PasswordRecoverDTO(VCodeBase):
    vcode: str
    new: str


class VerificationCodeDO(VCodeBase):
    id: int
    vcode: str
    is_active: bool
    expire_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime


class VerificationCodeCreateDO(VCodeBase):
    vcode: str
    expire_at: datetime.datetime
