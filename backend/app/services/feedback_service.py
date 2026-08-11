from typing import List
from sqlalchemy.orm import Session
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.user_repository import UserRepository
from app.models.models import User, Feedback


class FeedbackService:
    def __init__(self, db: Session) -> None:
        self.feedback_repo = FeedbackRepository(db)
        self.user_repo = UserRepository(db)

    def get_manager_submission_statuses(self, cycle_id: int, manager: User) -> List[dict]:
        """
        Returns one entry per direct report showing whether the manager has
        SUBMITTED, saved a DRAFT, or not started (PENDING) feedback for them.
        Reports list comes from User.manager_id — not inferred from past feedback.
        """
        cycle = self.feedback_repo.get_cycle(cycle_id, manager.company_id)
        if not cycle:
            raise ValueError("Cycle not found or does not belong to your company.")

        reports = self.user_repo.get_direct_reports(manager.id, manager.company_id)
        submissions = self.feedback_repo.get_submissions_by_manager(cycle_id, manager.id)
        sub_map = {s.given_to_id: s for s in submissions}

        result = []
        for report in reports:
            feedback = sub_map.get(report.id)
            result.append(
                {
                    "feedback_id": feedback.id if feedback else None,
                    "employee": report,
                    "status": feedback.status if feedback else "PENDING",
                    "submitted_at": feedback.submitted_at if feedback else None,
                    "scores": [
                        {"parameter_id": score.parameter_id, "score": score.score, "comment": score.comment}
                        for score in feedback.scores
                    ] if feedback else [],
                }
            )
        return result

    def submit_feedback(
        self,
        cycle_id: int,
        given_by: User,
        given_to_id: int,
        scores: List[dict],
        status: str,
    ) -> Feedback:
        """
        Business rules enforced here (not in the route layer):
          1. given_to must be a direct report of given_by (same company guaranteed).
          2. Cycle must belong to the same company.
          3. Cannot modify already-submitted feedback (enforced in repository).
        """
        reports = self.user_repo.get_direct_reports(given_by.id, given_by.company_id)
        if given_to_id not in {r.id for r in reports}:
            raise PermissionError(
                "You can only give feedback to your direct reports."
            )

        cycle = self.feedback_repo.get_cycle(cycle_id, given_by.company_id)
        if not cycle:
            raise ValueError("Cycle not found or does not belong to your company.")

        parameter_ids = [score["parameter_id"] for score in scores]
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ValueError("Each feedback parameter can be scored only once.")

        valid_parameter_ids = {p.id for p in self.feedback_repo.get_all_parameters()}
        invalid_ids = set(parameter_ids) - valid_parameter_ids
        if invalid_ids:
            raise ValueError("One or more feedback parameters are invalid.")

        if status == "SUBMITTED" and set(parameter_ids) != valid_parameter_ids:
            raise ValueError("Submitted feedback must include scores for all five parameters.")

        return self.feedback_repo.upsert_feedback(
            cycle_id=cycle_id,
            company_id=given_by.company_id,
            given_by_id=given_by.id,
            given_to_id=given_to_id,
            status=status,
            scores=scores,
        )

    def get_received_feedback(self, employee: User) -> List[dict]:
        feedbacks = self.feedback_repo.get_received_feedback(
            employee.id, employee.company_id
        )
        return [
            {
                "cycle_id": f.cycle_id,
                "month": f.cycle.month,
                "year": f.cycle.year,
                "status": f.status,
                "given_by_name": f.given_by.name,
                "scores": [
                    {
                        "parameter_id": s.parameter_id,
                        "parameter_name": s.parameter.name,
                        "score": s.score,
                        "comment": s.comment,
                    }
                    for s in f.scores
                ],
            }
            for f in feedbacks
        ]

    def get_parameter_trends(self, employee: User) -> List[dict]:
        """
        Per-parameter trend: each parameter gets its own time series.
        Scores are normalized rows, so this is a simple JOIN — no JSON unpacking.
        """
        feedbacks = self.feedback_repo.get_received_feedback(
            employee.id, employee.company_id
        )
        parameters = self.feedback_repo.get_all_parameters()

        param_scores: dict = {p.id: [] for p in parameters}
        for f in feedbacks:
            for s in f.scores:
                param_scores[s.parameter_id].append(
                    {"month": f.cycle.month, "year": f.cycle.year, "score": s.score}
                )

        return [
            {
                "parameter_id": p.id,
                "parameter_name": p.name,
                "monthly_scores": sorted(
                    param_scores[p.id], key=lambda x: (x["year"], x["month"])
                ),
            }
            for p in parameters
        ]
