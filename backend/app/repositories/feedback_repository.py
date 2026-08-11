from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Feedback, FeedbackScore, FeedbackCycle, FeedbackParameter


class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Cycles ────────────────────────────────────────────────────────────────

    def get_cycle(self, cycle_id: int, company_id: int) -> Optional[FeedbackCycle]:
        return (
            self.db.query(FeedbackCycle)
            .filter(FeedbackCycle.id == cycle_id, FeedbackCycle.company_id == company_id)
            .first()
        )

    def get_cycles_for_company(self, company_id: int) -> List[FeedbackCycle]:
        return (
            self.db.query(FeedbackCycle)
            .filter(FeedbackCycle.company_id == company_id)
            .order_by(FeedbackCycle.year.desc(), FeedbackCycle.month.desc())
            .all()
        )

    def get_latest_cycle(self, company_id: int) -> Optional[FeedbackCycle]:
        return (
            self.db.query(FeedbackCycle)
            .filter(FeedbackCycle.company_id == company_id)
            .order_by(FeedbackCycle.year.desc(), FeedbackCycle.month.desc())
            .first()
        )

    # ── Feedback ──────────────────────────────────────────────────────────────

    def get_feedback(
        self, cycle_id: int, given_by_id: int, given_to_id: int
    ) -> Optional[Feedback]:
        return (
            self.db.query(Feedback)
            .filter(
                Feedback.cycle_id == cycle_id,
                Feedback.given_by_id == given_by_id,
                Feedback.given_to_id == given_to_id,
            )
            .first()
        )

    def get_feedback_by_id(self, feedback_id: int, company_id: int) -> Optional[Feedback]:
        """Tenant-safe fetch by primary key."""
        return (
            self.db.query(Feedback)
            .filter(Feedback.id == feedback_id, Feedback.company_id == company_id)
            .first()
        )

    def get_submissions_by_manager(self, cycle_id: int, given_by_id: int) -> List[Feedback]:
        return (
            self.db.query(Feedback)
            .filter(Feedback.cycle_id == cycle_id, Feedback.given_by_id == given_by_id)
            .all()
        )

    def get_received_feedback(self, given_to_id: int, company_id: int) -> List[Feedback]:
        """Only SUBMITTED feedback is visible to the recipient."""
        return (
            self.db.query(Feedback)
            .join(FeedbackCycle, Feedback.cycle_id == FeedbackCycle.id)
            .filter(
                Feedback.given_to_id == given_to_id,
                Feedback.company_id == company_id,
                Feedback.status == "SUBMITTED",
            )
            .order_by(FeedbackCycle.year.desc(), FeedbackCycle.month.desc())
            .all()
        )

    def get_all_feedback_for_cycle(self, cycle_id: int, company_id: int) -> List[Feedback]:
        """Used by HR service to compute pending submissions."""
        return (
            self.db.query(Feedback)
            .filter(Feedback.cycle_id == cycle_id, Feedback.company_id == company_id)
            .all()
        )

    def get_all_parameters(self) -> List[FeedbackParameter]:
        return self.db.query(FeedbackParameter).order_by(FeedbackParameter.id).all()

    # ── Write ─────────────────────────────────────────────────────────────────

    def upsert_feedback(
        self,
        cycle_id: int,
        company_id: int,
        given_by_id: int,
        given_to_id: int,
        status: str,
        scores: List[dict],
    ) -> Feedback:
        existing = self.get_feedback(cycle_id, given_by_id, given_to_id)

        if existing:
            if existing.status == "SUBMITTED":
                raise ValueError("Cannot modify already-submitted feedback.")
            existing.status = status
            if status == "SUBMITTED":
                existing.submitted_at = datetime.now(timezone.utc)
            # Replace scores atomically
            self.db.query(FeedbackScore).filter(
                FeedbackScore.feedback_id == existing.id
            ).delete()
            for s in scores:
                self.db.add(
                    FeedbackScore(
                        feedback_id=existing.id,
                        parameter_id=s["parameter_id"],
                        score=s["score"],
                        comment=s["comment"],
                    )
                )
            self.db.flush()
            return existing
        else:
            feedback = Feedback(
                cycle_id=cycle_id,
                company_id=company_id,
                given_by_id=given_by_id,
                given_to_id=given_to_id,
                status=status,
                submitted_at=datetime.now(timezone.utc) if status == "SUBMITTED" else None,
            )
            self.db.add(feedback)
            self.db.flush()
            for s in scores:
                self.db.add(
                    FeedbackScore(
                        feedback_id=feedback.id,
                        parameter_id=s["parameter_id"],
                        score=s["score"],
                        comment=s["comment"],
                    )
                )
            self.db.flush()
            return feedback
