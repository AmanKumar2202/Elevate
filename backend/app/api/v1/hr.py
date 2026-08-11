from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_hr_user
from app.models.models import User
from app.services.hr_service import HRService
from app.repositories.feedback_repository import FeedbackRepository

router = APIRouter(prefix="/hr", tags=["hr"])


@router.get("/cycles")
def get_hr_cycles(
    current_user: User = Depends(get_current_hr_user),
    db: Session = Depends(get_db),
):
    repo = FeedbackRepository(db)
    cycles = repo.get_cycles_for_company(current_user.company_id)
    return [{"id": c.id, "month": c.month, "year": c.year} for c in cycles]


@router.get("/pending")
def get_pending_submissions(
    cycle_id: int,
    current_user: User = Depends(get_current_hr_user),
    db: Session = Depends(get_db),
):
    """
    Returns per-manager pending status for the requested cycle.
    Requires HR role — enforced by get_current_hr_user dependency.
    company_id is taken from the authenticated user (server-side only —
    never accepted from query params) to prevent cross-tenant access.
    """
    service = HRService(db)
    try:
        result = service.get_pending_submissions(cycle_id, current_user.company_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [
        {
            "manager": {
                "id": r["manager"].id,
                "name": r["manager"].name,
                "email": r["manager"].email,
                "title": r["manager"].title,
            },
            "total_reports": r["total_reports"],
            "submitted_count": r["submitted_count"],
            "pending_employees": [
                {"id": e.id, "name": e.name, "email": e.email, "title": e.title}
                for e in r["pending_employees"]
            ],
        }
        for r in result
    ]
