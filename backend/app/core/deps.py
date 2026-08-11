from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import decode_token
from app.models.models import User, RoleEnum

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator:
    """FastAPI dependency — yields a SQLAlchemy session and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve the current user from the JWT.
    company_id is taken from the DB record, NOT from the token payload,
    so client-side tampering cannot escalate privileges.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_hr_user(current_user: User = Depends(get_current_user)) -> User:
    """Guard: only HR-role users may pass."""
    if current_user.role != RoleEnum.HR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR role required for this endpoint.",
        )
    return current_user
