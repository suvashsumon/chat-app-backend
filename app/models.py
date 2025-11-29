from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    display_name = Column(String)
    hashed_password = Column(String)
    public_key = Column(String)
    avatar = Column(String, nullable=True)

    spaces = relationship("SpaceMember", back_populates="user")

class Space(Base):
    __tablename__ = "spaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))

    members = relationship("SpaceMember", back_populates="space")
    messages = relationship("Message", back_populates="space")

class SpaceMember(Base):
    __tablename__ = "space_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    space_id = Column(Integer, ForeignKey("spaces.id"))
    encrypted_space_key = Column(String)

    user = relationship("User", back_populates="spaces")
    space = relationship("Space", back_populates="members")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    space_id = Column(Integer, ForeignKey("spaces.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_deleted = Column(Integer, default=0)

    space = relationship("Space", back_populates="messages")
    sender = relationship("User")
