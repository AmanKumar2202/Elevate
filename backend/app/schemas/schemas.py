"""
Pydantic request/response schemas using model_config (Pydantic v2 style).
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ─── User ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    company_id: int
    company_name: str
    manager_id: Optional[int] = None
    title: Optional[str] = None
    has_reports: bool = False


class DirectReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    title: Optional[str] = None


# ─── FeedbackParameter ────────────────────────────────────────────────────────

class FeedbackParameterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None


# ─── FeedbackCycle ────────────────────────────────────────────────────────────

class FeedbackCycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    month: int
    year: int


# ─── Feedback ─────────────────────────────────────────────────────────────────

class ScoreIn(BaseModel):
    parameter_id: int
    score: int = Field(..., ge=1, le=5, description="Score from 1 (poor) to 5 (excellent)")
    comment: str = Field("", description="Optional written feedback")


class FeedbackSubmitRequest(BaseModel):
    cycle_id: int
    given_to_id: int
    scores: List[ScoreIn] = Field(default_factory=list)
    status: Literal["DRAFT", "SUBMITTED"] = "SUBMITTED"


class ScoreOut(BaseModel):
    parameter_id: int
    parameter_name: str
    score: int
    comment: str


class ManagerSubmissionStatus(BaseModel):
    feedback_id: Optional[int]
    employee: DirectReport
    status: str  # SUBMITTED | DRAFT | PENDING
    submitted_at: Optional[datetime] = None


# ─── HR ───────────────────────────────────────────────────────────────────────

class ManagerPendingReport(BaseModel):
    manager: DirectReport
    total_reports: int
    submitted_count: int
    pending_employees: List[DirectReport]


# ─── Employee Received Feedback ───────────────────────────────────────────────

class ReceivedFeedbackItem(BaseModel):
    cycle_id: int
    month: int
    year: int
    status: str
    given_by_name: str
    scores: List[ScoreOut]


# ─── Trends ───────────────────────────────────────────────────────────────────

class MonthlyScore(BaseModel):
    month: int
    year: int
    score: int


class ParameterTrend(BaseModel):
    parameter_id: int
    parameter_name: str
    monthly_scores: List[MonthlyScore]
