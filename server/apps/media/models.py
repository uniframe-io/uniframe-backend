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


class Media(Base):
    __tablename__ = "medias"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location = Column(String(200))
    ext_info = Column(Text)
    e_tag = Column(String(200))
    content_type = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
