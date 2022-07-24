from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import Boolean
from sqlalchemy.types import DateTime, Integer, String, Text

from server.libs.db.sqlalchemy import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200))
    description = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    ext_info = Column(Text)


class GroupMembers(Base):
    __tablename__ = "group_members"
    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    group_id = Column(Integer, ForeignKey("groups.id"))
    member_id = Column(Integer, ForeignKey("users.id"))
