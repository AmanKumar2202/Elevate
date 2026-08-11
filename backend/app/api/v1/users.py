from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.models.models import User
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's profile, including whether they have reports."""
    repo = UserRepository(db)
    reports = repo.get_direct_reports(current_user.id, current_user.company_id)
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "company_id": current_user.company_id,
        "company_name": current_user.company.name,
        "manager_id": current_user.manager_id,
        "title": current_user.title,
        "has_reports": len(reports) > 0,
    }


@router.get("/my-reports")
def get_my_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's direct reports (empty list if none)."""
    repo = UserRepository(db)
    reports = repo.get_direct_reports(current_user.id, current_user.company_id)
    return [
        {"id": r.id, "name": r.name, "email": r.email, "title": r.title}
        for r in reports
    ]
