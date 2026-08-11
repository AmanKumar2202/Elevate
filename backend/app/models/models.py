import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Text,
    UniqueConstraint,
    CheckConstraint,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class RoleEnum(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    HR = "HR"


class FeedbackStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"


class Company(Base):
    """One row per tenant.  All other tables reference company_id for isolation."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)

    users = relationship("User", back_populates="company")
    feedback_cycles = relationship("FeedbackCycle", back_populates="company")


class User(Base):
    """
    Single entity for everyone in the org.
    manager_id is a self-referencing FK (nullable for top of org / HR).
    role is ORTHOGONAL to manager_id:
      - A manager is just an EMPLOYEE whose id appears as another user's manager_id.
      - HR is a cross-cutting role that sits outside the reporting hierarchy.
    This allows Priya to both give feedback (manager of 6) and receive it (reports to Rohan)
    without any special-casing in code.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    # Stored as VARCHAR so the model works with both PostgreSQL and SQLite (tests)
    role = Column(String(20), nullable=False, default=RoleEnum.EMPLOYEE.value)
    manager_id = Column(Integer, nullable=True, index=True)
    title = Column(String(255), nullable=True)

    company = relationship("Company", back_populates="users")
    manager = relationship(
        "User", remote_side=[id], back_populates="reports", overlaps="company,users"
    )
    reports = relationship("User", back_populates="manager", overlaps="company,users")
    feedback_given = relationship(
        "Feedback", foreign_keys="Feedback.given_by_id", back_populates="given_by"
    )

    __table_args__ = (
        # Makes an accidental cross-company reporting relationship impossible.
        UniqueConstraint("id", "company_id", name="uq_user_id_company"),
        ForeignKeyConstraint(
            ["manager_id", "company_id"], ["users.id", "users.company_id"],
            name="fk_user_manager_same_company",
        ),
    )
    feedback_received = relationship(
        "Feedback", foreign_keys="Feedback.given_to_id", back_populates="given_to"
    )


class FeedbackParameter(Base):
    """Fixed global parameters (Ownership, Communication, etc.)."""

    __tablename__ = "feedback_parameters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    scores = relationship("FeedbackScore", back_populates="parameter")


class FeedbackCycle(Base):
    """
    One cycle = one calendar month for one company.
    unique(company_id, month, year) prevents duplicate cycles.
    Used as source of truth for 'expected' feedback pairs when deriving
    who-hasn't-submitted (via User.manager_id, not via past feedback rows).
    """

    __tablename__ = "feedback_cycles"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "month", "year", name="uq_cycle_company_month_year"),
        UniqueConstraint("id", "company_id", name="uq_cycle_id_company"),
    )

    company = relationship("Company", back_populates="feedback_cycles")
    feedbacks = relationship("Feedback", back_populates="cycle")


class Feedback(Base):
    """
    One row per (manager, employee, cycle) triple.
    company_id is denormalized for fast tenant-isolated queries.
    Status: DRAFT (saved, not final) or SUBMITTED (locked).
    DB constraint prevents self-feedback at the data layer.
    """

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    given_by_id = Column(Integer, nullable=False, index=True)
    given_to_id = Column(Integer, nullable=False, index=True)
    status = Column(String(20), nullable=False, default=FeedbackStatusEnum.DRAFT.value)
    submitted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "cycle_id", "given_by_id", "given_to_id",
            name="uq_feedback_cycle_giver_receiver",
        ),
        CheckConstraint("given_by_id != given_to_id", name="ck_no_self_feedback"),
        ForeignKeyConstraint(
            ["cycle_id", "company_id"], ["feedback_cycles.id", "feedback_cycles.company_id"],
            name="fk_feedback_cycle_same_company",
        ),
        ForeignKeyConstraint(
            ["given_by_id", "company_id"], ["users.id", "users.company_id"],
            name="fk_feedback_giver_same_company",
        ),
        ForeignKeyConstraint(
            ["given_to_id", "company_id"], ["users.id", "users.company_id"],
            name="fk_feedback_receiver_same_company",
        ),
    )

    cycle = relationship("FeedbackCycle", back_populates="feedbacks")
    given_by = relationship(
        "User", foreign_keys=[given_by_id], back_populates="feedback_given"
    )
    given_to = relationship(
        "User", foreign_keys=[given_to_id], back_populates="feedback_received"
    )
    scores = relationship(
        "FeedbackScore", back_populates="feedback", cascade="all, delete-orphan"
    )


class FeedbackScore(Base):
    """
    One row per (feedback, parameter) pair.
    Normalized rows (not JSON) so trend queries are simple:
      SELECT parameter_id, score, cycle.month FROM feedback_scores
      JOIN feedbacks ... WHERE given_to_id = X ORDER BY cycle.month
    """

    __tablename__ = "feedback_scores"

    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(Integer, ForeignKey("feedbacks.id"), nullable=False, index=True)
    parameter_id = Column(
        Integer, ForeignKey("feedback_parameters.id"), nullable=False, index=True
    )
    score = Column(Integer, nullable=False)  # 1–5
    comment = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("feedback_id", "parameter_id", name="uq_score_feedback_parameter"),
        CheckConstraint("score >= 1 AND score <= 5", name="ck_score_range_1_5"),
    )

    feedback = relationship("Feedback", back_populates="scores")
    parameter = relationship("FeedbackParameter", back_populates="scores")
