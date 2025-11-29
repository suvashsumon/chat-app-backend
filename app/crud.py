from sqlalchemy.orm import Session
from . import models, schemas
import bcrypt

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    print(f"[DEBUG] Registering user: {user.username}")
    print(f"[DEBUG] Plain password (truncated): {user.password[:72]}")
    hashed_password_bytes = bcrypt.hashpw(user.password.encode('utf-8')[:72], bcrypt.gensalt())
    hashed_password_str = hashed_password_bytes.decode('utf-8')
    print(f"[DEBUG] Hashed password (bytes): {hashed_password_bytes}")
    print(f"[DEBUG] Hashed password (string to store): {hashed_password_str}")
    db_user = models.User(
        username=user.username,
        display_name=user.display_name,
        hashed_password=hashed_password_str,
        public_key=user.public_key,
        avatar=user.avatar
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_password(db: Session, user_id: int, new_hashed_password: str):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.hashed_password = new_hashed_password
        db.commit()
        db.refresh(db_user)
    return db_user

def get_spaces_for_user(db: Session, user_id: int):
    print(f"[DEBUG Backend] Entering get_spaces_for_user for user_id: {user_id}")
    results = db.query(
                models.Space,
                models.SpaceMember.encrypted_space_key,
                models.User.display_name.label("creator_display_name") # Fetch creator's display name
             ) \
             .join(models.SpaceMember, models.Space.id == models.SpaceMember.space_id) \
             .join(models.User, models.Space.created_by == models.User.id) \
             .filter(models.SpaceMember.user_id == user_id) \
             .all()
    
    print(f"[DEBUG Backend] get_spaces_for_user raw results: {results}")

    spaces_with_info = []
    for space, encrypted_space_key, creator_display_name in results:
        space_data = schemas.Space.from_orm(space).dict()
        space_data["encrypted_space_key"] = encrypted_space_key
        space_data["creator_display_name"] = creator_display_name # Add creator's display name
        spaces_with_info.append(schemas.SpaceWithMemberInfo(**space_data))
    return spaces_with_info

def create_space(db: Session, space: schemas.SpaceCreate, user_id: int, encrypted_space_key: str):
    db_space = models.Space(**space.dict(), created_by=user_id)
    db.add(db_space)
    db.commit()
    db.refresh(db_space)

    # Automatically add the creator as a member of the space with the provided encrypted_space_key
    db_space_member = models.SpaceMember(
        space_id=db_space.id,
        user_id=user_id,
        encrypted_space_key=encrypted_space_key
    )
    db.add(db_space_member)
    db.commit()
    db.refresh(db_space_member)

    return db_space

def add_user_to_space(db: Session, space_id: int, user_id: int, encrypted_space_key: str):
    db_space_member = models.SpaceMember(
        space_id=space_id,
        user_id=user_id,
        encrypted_space_key=encrypted_space_key
    )
    db.add(db_space_member)
    db.commit()
    db.refresh(db_space_member)
    return db_space_member

def get_space_members(db: Session, space_id: int):
    return db.query(models.User).join(models.SpaceMember).filter(models.SpaceMember.space_id == space_id).all()

def get_messages_for_space(db: Session, space_id: int):
    results = db.query(models.Message, models.User.display_name) \
             .join(models.User, models.Message.sender_id == models.User.id) \
             .filter(models.Message.space_id == space_id) \
             .order_by(models.Message.timestamp) \
             .all()
    
    # Manually map the results to a list of dictionaries compatible with schemas.Message
    messages_with_sender_info = []
    for message, sender_display_name in results:
        message_dict = message.__dict__
        message_dict["sender_display_name"] = sender_display_name
        # Remove SQLAlchemy internal state
        message_dict.pop('_sa_instance_state', None)
        messages_with_sender_info.append(message_dict)
    return messages_with_sender_info

def create_message(db: Session, space_id: int, sender_id: int, content: str):
    print(f"[DEBUG] CRUD: Creating message for space {space_id} by sender {sender_id}")
    print(f"[DEBUG] CRUD: Message content: {content}")
    db_message = models.Message(
        space_id=space_id,
        sender_id=sender_id,
        content=content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def delete_message(db: Session, message_id: int):
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
    db_message.is_deleted = 1
    db.commit()
    db.refresh(db_message)
    return db_message