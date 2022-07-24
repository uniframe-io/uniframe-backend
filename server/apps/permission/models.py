from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from server.libs.db.sqlalchemy import Base


class LocalDeployUser(Base):
    __tablename__ = "local_deploy_users"

    id = Column(
        Integer, primary_key=True, index=True, server_default=func.next_id()
    )
    email = Column(String(200))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=False)
    company = Column(String(200))
    role = Column(String(200))
    purpose = Column(String(200))
    requested_at = Column(DateTime, server_default=func.now(), nullable=False)
    approved_at = Column(DateTime)
    expire_at = Column(DateTime)
