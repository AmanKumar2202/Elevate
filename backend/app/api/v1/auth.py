from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db
from app.schemas.schemas import LoginRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Single login endpoint for all companies.
    Company identity is resolved server-side from the authenticated user record.
    The JWT payload includes company_id for logging, but every DB query
    re-derives it from the user row — never from client input.
    """
    service = AuthService(db)
    user = service.authenticate(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    token = service.create_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "company_id": user.company_id,
            "company_name": user.company.name,
            "manager_id": user.manager_id,
            "title": user.title,
        },
    }
