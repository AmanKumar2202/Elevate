from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_direct_reports(self, manager_id: int, company_id: int) -> List[User]:
        """
        Returns users whose manager_id == manager_id AND company_id matches.
        company_id guard prevents cross-tenant leakage if a manager ID is guessed.
        """
        return (
            self.db.query(User)
            .filter(User.manager_id == manager_id, User.company_id == company_id)
            .all()
        )

    def get_all_managers_in_company(self, company_id: int) -> List[User]:
        """
        Returns every user who is referenced as manager_id by at least one
        other user in the same company.  This is the source of truth used by
        the HR 'who hasn't submitted' query — a manager with zero feedback rows
        this cycle will still appear here.
        """
        # Use select() explicitly to avoid SAWarning on subquery coercion
        manager_id_subq = (
            select(User.manager_id)
            .where(User.manager_id.isnot(None), User.company_id == company_id)
            .distinct()
            .scalar_subquery()
        )
        return (
            self.db.query(User)
            .filter(User.id.in_(manager_id_subq), User.company_id == company_id)
            .all()
        )
