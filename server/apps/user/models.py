from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from server.apps.user import schemas
from server.libs.db.sqlalchemy import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    email = Column(String(200))
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    login_type = Column(String(20), default=schemas.LOGIN_TYPE.EMAIL)
    ext_info = Column(JSON)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
