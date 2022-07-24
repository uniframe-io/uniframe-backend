import datetime
from typing import List

from pydantic import BaseModel


class GroupBase(BaseModel):
    name: str
    description: str


class GroupCreateDTO(GroupBase):
    """
    create group API input
    """

    pass


class GroupCreateDO(GroupBase):
    """
    create group domain object
    """

    pass


class GroupDTO(GroupBase):
    """
    get group response schema to frontend
    """

    id: int
    owner_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class GroupDO(GroupDTO):
    """
    Get group domain object
    """

    is_active: bool


class GroupUpdateDTO(GroupBase):
    """
    Update group endpoint input
    """

    pass


class GroupUpdateDO(GroupBase):
    pass


# class GroupMembersBase(BaseModel):
#     group_id: int
#     member_id: int


# class GroupMembersAddDO(GroupMembersBase):
#     pass


# class GroupMembersDeleteDO(GroupMembersBase):
#     pass


# class GroupMemberDO(GroupMembersBase):
#     pass


class GroupMembersDO(BaseModel):
    group_id: int
    members: List[int]


class GroupMembersDTO(GroupMembersDO):
    pass
