from typing import List
from sqlalchemy.orm import Session
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.user_repository import UserRepository


class HRService:
    def __init__(self, db: Session) -> None:
        self.feedback_repo = FeedbackRepository(db)
        self.user_repo = UserRepository(db)

    def get_pending_submissions(self, cycle_id: int, company_id: int) -> List[dict]:
        """
        For a given cycle, return per-manager submission status.

        Key design:  We derive 'expected pairs' from User.manager_id
        (not from existing feedback rows), so a manager who submitted zero
        feedback this month still shows up with a full pending list.
        This is the correct answer to 'who hasn't submitted' as described
        in the roadmap.

        Algorithm:
          1. Get all users referenced as a manager_id in this company.
          2. For each manager, get their direct reports from User.manager_id.
          3. LEFT JOIN against submitted Feedback rows for this cycle.
          4. Missing rows = pending.
        """
        cycle = self.feedback_repo.get_cycle(cycle_id, company_id)
        if not cycle:
            raise ValueError("Cycle not found or does not belong to your company.")

        managers = self.user_repo.get_all_managers_in_company(company_id)
        all_feedbacks = self.feedback_repo.get_all_feedback_for_cycle(cycle_id, company_id)

        # Only SUBMITTED rows count as 'done'
        submitted_pairs = {
            (f.given_by_id, f.given_to_id)
            for f in all_feedbacks
            if f.status == "SUBMITTED"
        }

        result = []
        for manager in managers:
            reports = self.user_repo.get_direct_reports(manager.id, company_id)
            pending = [r for r in reports if (manager.id, r.id) not in submitted_pairs]

            result.append(
                {
                    "manager": manager,
                    "total_reports": len(reports),
                    "submitted_count": len(reports) - len(pending),
                    "pending_employees": pending,
                }
            )

        return result
