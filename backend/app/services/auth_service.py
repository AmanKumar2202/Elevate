from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.models.models import User


class AuthService:
    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_token(self, user: User) -> str:
        """
        The JWT carries user_id, company_id, and role.
        company_id in the JWT is used only for logging — the authoritative
        company_id is always re-fetched from the DB on each request so that
        client-side tampering cannot escalate cross-tenant access.
        """
        return create_access_token(
            data={
                "sub": str(user.id),
                "company_id": user.company_id,
                "role": user.role,
            }
        )
