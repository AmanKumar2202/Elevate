"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-08-11 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── companies ─────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_companies_id", "companies", ["id"], unique=False)

    # ── users (self-referencing via manager_id) ───────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(
            ["manager_id", "company_id"], ["users.id", "users.company_id"],
            name="fk_user_manager_same_company",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("id", "company_id", name="uq_user_id_company"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_company_id", "users", ["company_id"], unique=False)
    op.create_index("ix_users_manager_id", "users", ["manager_id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── feedback_parameters ───────────────────────────────────────────────────
    op.create_table(
        "feedback_parameters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedback_parameters_id", "feedback_parameters", ["id"], unique=False)

    # ── feedback_cycles ───────────────────────────────────────────────────────
    op.create_table(
        "feedback_cycles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "month", "year", name="uq_cycle_company_month_year"
        ),
        sa.UniqueConstraint("id", "company_id", name="uq_cycle_id_company"),
    )
    op.create_index("ix_feedback_cycles_id", "feedback_cycles", ["id"], unique=False)
    op.create_index(
        "ix_feedback_cycles_company_id", "feedback_cycles", ["company_id"], unique=False
    )

    # ── feedbacks ─────────────────────────────────────────────────────────────
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cycle_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("given_by_id", sa.Integer(), nullable=False),
        sa.Column("given_to_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("given_by_id != given_to_id", name="ck_no_self_feedback"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(
            ["cycle_id", "company_id"], ["feedback_cycles.id", "feedback_cycles.company_id"],
            name="fk_feedback_cycle_same_company",
        ),
        sa.ForeignKeyConstraint(
            ["given_by_id", "company_id"], ["users.id", "users.company_id"],
            name="fk_feedback_giver_same_company",
        ),
        sa.ForeignKeyConstraint(
            ["given_to_id", "company_id"], ["users.id", "users.company_id"],
            name="fk_feedback_receiver_same_company",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cycle_id", "given_by_id", "given_to_id",
            name="uq_feedback_cycle_giver_receiver",
        ),
    )
    op.create_index("ix_feedbacks_id", "feedbacks", ["id"], unique=False)
    op.create_index("ix_feedbacks_cycle_id", "feedbacks", ["cycle_id"], unique=False)
    op.create_index("ix_feedbacks_company_id", "feedbacks", ["company_id"], unique=False)
    op.create_index("ix_feedbacks_given_by_id", "feedbacks", ["given_by_id"], unique=False)
    op.create_index("ix_feedbacks_given_to_id", "feedbacks", ["given_to_id"], unique=False)

    # ── feedback_scores ───────────────────────────────────────────────────────
    op.create_table(
        "feedback_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("feedback_id", sa.Integer(), nullable=False),
        sa.Column("parameter_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.CheckConstraint("score >= 1 AND score <= 5", name="ck_score_range_1_5"),
        sa.ForeignKeyConstraint(["feedback_id"], ["feedbacks.id"]),
        sa.ForeignKeyConstraint(["parameter_id"], ["feedback_parameters.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "feedback_id", "parameter_id", name="uq_score_feedback_parameter"
        ),
    )
    op.create_index("ix_feedback_scores_id", "feedback_scores", ["id"], unique=False)
    op.create_index(
        "ix_feedback_scores_feedback_id", "feedback_scores", ["feedback_id"], unique=False
    )
    op.create_index(
        "ix_feedback_scores_parameter_id",
        "feedback_scores",
        ["parameter_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("feedback_scores")
    op.drop_table("feedbacks")
    op.drop_table("feedback_cycles")
    op.drop_table("feedback_parameters")
    op.drop_table("users")
    op.drop_table("companies")
