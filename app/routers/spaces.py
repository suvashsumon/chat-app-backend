from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, auth, database, models

router = APIRouter()

@router.post("/spaces/", response_model=schemas.Space)
def create_space(
    space: schemas.SpaceCreate,
    encrypted_space_key: str, # New parameter for the creator's encrypted key
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.create_space(db=db, space=space, user_id=current_user.id, encrypted_space_key=encrypted_space_key)

@router.get("/spaces/me", response_model=List[schemas.SpaceWithMemberInfo])
def read_my_spaces(db: Session = Depends(database.get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    return crud.get_spaces_for_user(db=db, user_id=current_user.id)

@router.post("/spaces/{space_id}/add_member")
def add_member_to_space(
    space_id: int,
    member_data: schemas.SpaceMemberCreate,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    space = db.query(models.Space).filter(models.Space.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    if space.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only space creator can add members")

    user_to_add = crud.get_user_by_username(db, username=member_data.username)
    if not user_to_add:
        raise HTTPException(status_code=404, detail="User not found")

    crud.add_user_to_space(db=db, space_id=space_id, user_id=user_to_add.id, encrypted_space_key=member_data.encrypted_space_key)
    return {"message": f"User {member_data.username} added to space {space.name}"}

@router.get("/spaces/{space_id}/members", response_model=List[schemas.User])
def get_space_members(space_id: int, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    # Add logic to check if current_user is a member of the space
    is_member = db.query(models.SpaceMember).filter(
        models.SpaceMember.space_id == space_id,
        models.SpaceMember.user_id == current_user.id
    ).first()
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this space")

    return crud.get_space_members(db=db, space_id=space_id)
