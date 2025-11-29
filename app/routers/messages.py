from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, auth, database, websocket_manager, models
import json

router = APIRouter()

@router.post("/messages/", response_model=schemas.Message)
async def create_message(
    message: schemas.MessageCreate,
    space_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    print(f"[DEBUG] Received message for space {space_id} from user {current_user.id}")
    print(f"[DEBUG] Message content (encrypted): {message.content}")
    # TODO: Check if current_user is a member of the space
    db_message = crud.create_message(db=db, space_id=space_id, sender_id=current_user.id, content=message.content)
    
    # Fetch sender's display name for broadcasting
    sender = db.query(models.User).filter(models.User.id == db_message.sender_id).first()
    sender_display_name = sender.display_name if sender else "Unknown User"

    # Convert SQLAlchemy model to Pydantic schema and add sender_display_name
    message_data = schemas.Message.from_orm(db_message)
    message_data.sender_display_name = sender_display_name

    print(f"[DEBUG] Message data before JSON dump: {message_data.dict()}")
    # Use Pydantic's .json() method for proper datetime serialization
    await websocket_manager.manager.broadcast(message_data.json(), space_id)
    return db_message

@router.get("/messages/{space_id}", response_model=List[schemas.Message])
def get_messages(
    space_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    # TODO: Check if current_user is a member of the space
    messages_with_sender_info = crud.get_messages_for_space(db=db, space_id=space_id)
    return [schemas.Message(**msg) for msg in messages_with_sender_info]

@router.delete("/messages/{message_id}", response_model=schemas.Message)
async def delete_message(
    message_id: int,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if current_user is the sender of the message
    if db_message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")

    deleted_message = crud.delete_message(db=db, message_id=message_id)
    # Broadcast the deleted message status
    deleted_message_data = schemas.Message.from_orm(deleted_message)
    # Ensure sender_display_name is included for broadcast if needed by frontend
    sender = db.query(models.User).filter(models.User.id == deleted_message.sender_id).first()
    deleted_message_data.sender_display_name = sender.display_name if sender else "Unknown User"
    await websocket_manager.manager.broadcast(deleted_message_data.json(), deleted_message.space_id)
    return deleted_message
