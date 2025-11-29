from pydantic import BaseModel
from typing import List, Optional
import datetime

class UserBase(BaseModel):
    username: str
    display_name: str
    public_key: str
    avatar: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True # Keep for now, but Pydantic v2 prefers from_attributes
        from_attributes = True

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str

class SpaceBase(BaseModel):
    name: str

class SpaceCreate(SpaceBase):
    pass

class Space(SpaceBase):
    id: int
    created_by: int

    class Config:
        orm_mode = True # Keep for now, but Pydantic v2 prefers from_attributes
        from_attributes = True

class SpaceMember(BaseModel):
    user_id: int
    space_id: int
    encrypted_space_key: str # Added encrypted_space_key

    class Config:
        orm_mode = True
        from_attributes = True

class SpaceWithMemberInfo(Space):
    encrypted_space_key: str
    creator_display_name: Optional[str] = None # Added creator_display_name

    class Config:
        orm_mode = True
        from_attributes = True

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    space_id: int
    sender_id: int
    timestamp: datetime.datetime
    is_deleted: int
    sender_display_name: Optional[str] = None # Added sender_display_name

    class Config:
        orm_mode = True # Keep for now, but Pydantic v2 prefers from_attributes
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SpaceMemberCreate(BaseModel):
    username: str
    encrypted_space_key: str
