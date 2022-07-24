import datetime
import enum
from typing import Optional

from pydantic import BaseModel, EmailStr


class LOGIN_TYPE(str, enum.Enum):
    EMAIL = "email"
    OAUTH2_GITHUB = "oauth2_github"
    OAUTH2_GOOGLE = "oauth2_google"


class UserBase(BaseModel):
    email: Optional[EmailStr]
    full_name: str


class UserDTO(UserBase):
    id: int
    login_type: str
    created_at: datetime.datetime


class UserDO(UserBase):
    id: int
    is_active: bool = True
    login_type: str
    hashed_password: Optional[str]
    is_superuser: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserCreateDTO(UserBase):
    email: EmailStr
    password: str
    vcode: str


class UserCreateDO(UserBase):
    login_type: str
    hashed_password: str


class UserUpdateDTO(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    hashed_password: Optional[str] = None


class UserUpdateDO(UserUpdateDTO):
    is_active: bool = True


class UserResetPasswordDTO(BaseModel):
    old_password: str
    new_password: str


# class USER_GROUP(str, enum.Enum):
#     ADMIN = "admin"
#     NORMAL_USER = "user"


# class USER_TYPE(str, enum.Enum):
#     USER = "user"
#     VISITOR = "visitor"
