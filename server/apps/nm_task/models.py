from sqlalchemy import Column, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import Boolean
from sqlalchemy.types import DateTime, Integer, String, Text

from server.libs.db.sqlalchemy import Base


class AbcXyzTask(Base):
    __tablename__ = "abcxyz_tasks"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200))
    description = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean)
    type = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    ext_info = Column(Text)


# # N.B.: membe_id should be active user
# class AbcXyzTaskUsers:
#     __tablename__ = "abcxyz_tasks_users"

#     abcxyz_task_id = Column(
#         Integer, ForeignKey("abcxyz_tasks.id", nullable=False)
#     )
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


# # N.B.: membe_id should be active user
# class AbcXyzTaskssGroups:
#     __tablename__ = "abcxyz_tasks_groups"

#     abcxyz_task_id = Column(
#         Integer, ForeignKey("abcxyz_tasks.id", nullable=False)
#     )
#     group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)


class AbcXyzTaskRunHistory(Base):
    __tablename__ = "abcxyz_tasks_run_history"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("abcxyz_tasks.id"), nullable=False)
    pod_name = Column(String(200), unique=True)
    pod_status = Column(String(30))
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    finished_at = Column(DateTime, nullable=True)
    ext_info = Column(Text)
