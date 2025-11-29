from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import crud, schemas, auth, database, models
import bcrypt # Import bcrypt

router = APIRouter()

@router.post("/users/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@router.post("/users/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    print(f"[DEBUG] Login attempt for username: {form_data.username}")
    print(f"[DEBUG] Login password (from form): {form_data.password}")
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user:
        print(f"[DEBUG] User {form_data.username} not found.")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not auth.verify_password(form_data.password, user.hashed_password):
        print(f"[DEBUG] Password mismatch for user {form_data.username}.")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

@router.get("/users/{username}/public_key", response_model=schemas.User)
def get_user_public_key(username: str, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/me/password", response_model=schemas.User)
async def change_password(
    password_change: schemas.UserPasswordChange,
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    # Verify current password
    if not auth.verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Hash new password
    new_hashed_password_bytes = bcrypt.hashpw(password_change.new_password.encode('utf-8')[:72], bcrypt.gensalt())
    new_hashed_password_str = new_hashed_password_bytes.decode('utf-8')

    # Update password in DB
    updated_user = crud.update_user_password(db, current_user.id, new_hashed_password_str)
    return updated_user
