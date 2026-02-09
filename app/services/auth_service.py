from sqlalchemy.orm import Session
from app.db.models import User
from app.core.password import hash_password, verify_password
from app.core.security import create_access_token

def register_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if user:
        return False

    new_user = User(
        username=username,
        hashed_password=hash_password(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return True

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return create_access_token({"sub": user.username})
