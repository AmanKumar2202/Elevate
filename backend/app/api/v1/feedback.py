from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.models.models import User
from app.repositories.feedback_repository import FeedbackRepository
from app.services.feedback_service import FeedbackService
from app.schemas.schemas import FeedbackSubmitRequest

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.get("/parameters")
def get_parameters(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),  # requires auth
):
    repo = FeedbackRepository(db)
    params = repo.get_all_parameters()
    return [{"id": p.id, "name": p.name, "description": p.description} for p in params]


@router.get("/cycles")
def get_cycles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = FeedbackRepository(db)
    cycles = repo.get_cycles_for_company(current_user.company_id)
    return [{"id": c.id, "month": c.month, "year": c.year} for c in cycles]


@router.get("/cycles/current")
def get_current_cycle(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = FeedbackRepository(db)
    cycle = repo.get_latest_cycle(current_user.company_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="No feedback cycles found.")
    return {"id": cycle.id, "month": cycle.month, "year": cycle.year}


@router.get("/my-submissions")
def get_my_submissions(
    cycle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns submission status for each of the current manager's direct reports.
    Status: SUBMITTED | DRAFT | PENDING (not started).
    Uses User.manager_id — managers with zero feedback rows still appear.
    """
    service = FeedbackService(db)
    try:
        statuses = service.get_manager_submission_statuses(cycle_id, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [
        {
            "feedback_id": s["feedback_id"],
            "employee": {
                "id": s["employee"].id,
                "name": s["employee"].name,
                "email": s["employee"].email,
                "title": s["employee"].title,
            },
            "status": s["status"],
            "submitted_at": (
                s["submitted_at"].isoformat() if s["submitted_at"] else None
            ),
            "scores": s["scores"],
        }
        for s in statuses
    ]


@router.post("/submit")
def submit_feedback(
    request: FeedbackSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update a feedback record (draft or submit)."""
    service = FeedbackService(db)
    try:
        feedback = service.submit_feedback(
            cycle_id=request.cycle_id,
            given_by=current_user,
            given_to_id=request.given_to_id,
            scores=[s.model_dump() for s in request.scores],
            status=request.status,
        )
        db.commit()
        return {"id": feedback.id, "status": feedback.status}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/received")
def get_received_feedback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all submitted feedback the current user has received."""
    service = FeedbackService(db)
    return service.get_received_feedback(current_user)


@router.get("/trends")
def get_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return per-parameter score trends for the current user over all cycles."""
    service = FeedbackService(db)
    return service.get_parameter_trends(current_user)


@router.get("/received/{feedback_id}")
def get_feedback_detail(
    feedback_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch a single feedback record — only visible to giver or receiver."""
    repo = FeedbackRepository(db)
    # company_id guard — prevents cross-tenant ID guessing
    feedback = repo.get_feedback_by_id(feedback_id, current_user.company_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found.")
    if feedback.given_to_id != current_user.id and feedback.given_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this feedback.")
    return {
        "id": feedback.id,
        "cycle": {
            "id": feedback.cycle.id,
            "month": feedback.cycle.month,
            "year": feedback.cycle.year,
        },
        "given_by": {"id": feedback.given_by.id, "name": feedback.given_by.name},
        "given_to": {"id": feedback.given_to.id, "name": feedback.given_to.name},
        "status": feedback.status,
        "submitted_at": feedback.submitted_at,
        "scores": [
            {
                "parameter_id": s.parameter_id,
                "parameter_name": s.parameter.name,
                "score": s.score,
                "comment": s.comment,
            }
            for s in feedback.scores
        ],
    }
