from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from server.libs.db.sqlalchemy import Base


class OAuth2User(Base):
    __tablename__ = "oauth2_users"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    provider_id = Column(Integer)
    provider = Column(String(20))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ext_info = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    action = Column(String(30))
    email = Column(String(200))
    vcode = Column(String(30))
    is_active = Column(Boolean, default=True)
    expire_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
