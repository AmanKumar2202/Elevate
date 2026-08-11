"""
Seed script — creates both companies with realistic org structures,
3 months of cycles, and deliberately incomplete submissions for the
July 2026 cycle so the HR dashboard has something real to catch.

Run standalone:  python -m app.db.seed
Auto-runs:       uvicorn startup event (idempotent — skips if already seeded)
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import (
    Company,
    User,
    FeedbackParameter,
    FeedbackCycle,
    Feedback,
    FeedbackScore,
    RoleEnum,
    FeedbackStatusEnum,
)
from app.core.security import get_password_hash


def seed_database(db: Session) -> None:
    # ── Idempotency guard ──────────────────────────────────────────────────
    if db.query(Company).count() > 0:
        print("Database already seeded. Skipping.")
        return

    print("Seeding database...")

    # ── 1. Feedback Parameters (global, 5 fixed) ───────────────────────────
    parameters = [
        FeedbackParameter(
            name="Ownership",
            description="Takes responsibility for outcomes and drives tasks to completion without constant supervision.",
        ),
        FeedbackParameter(
            name="Communication",
            description="Articulates ideas clearly, listens actively, and adapts style to audience.",
        ),
        FeedbackParameter(
            name="Quality of Work",
            description="Delivers accurate, thorough, and well-crafted output that meets or exceeds standards.",
        ),
        FeedbackParameter(
            name="Problem Solving",
            description="Identifies issues proactively and develops effective, creative solutions.",
        ),
        FeedbackParameter(
            name="Collaboration",
            description="Works effectively with teammates, shares knowledge, and contributes to a positive team culture.",
        ),
    ]
    db.add_all(parameters)
    db.flush()

    # ── 2. Ashoka Textiles — 3-level hierarchy ─────────────────────────────
    ashoka = Company(name="Ashoka Textiles")
    db.add(ashoka)
    db.flush()

    rohan = User(
        company_id=ashoka.id,
        name="Rohan Mehta",
        email="rohan@ashoka.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=None,
        title="VP Engineering (reports to COO)",
    )
    db.add(rohan)
    db.flush()

    priya = User(
        company_id=ashoka.id,
        name="Priya Sharma",
        email="priya@ashoka.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=rohan.id,
        title="Engineering Manager",
    )
    db.add(priya)
    db.flush()

    report_specs = [
        ("Aditya Verma", "aditya@ashoka.com", "Software Engineer"),
        ("Sneha Patel", "sneha@ashoka.com", "Software Engineer"),
        ("Vikram Singh", "vikram@ashoka.com", "Senior Developer"),
        ("Meena Raj", "meena@ashoka.com", "Frontend Developer"),
        ("Ravi Kumar", "ravi@ashoka.com", "Backend Developer"),
        ("Pooja Nair", "pooja@ashoka.com", "QA Engineer"),
    ]
    ashoka_reports: list[User] = []
    for name, email, title in report_specs:
        u = User(
            company_id=ashoka.id,
            name=name,
            email=email,
            hashed_password=get_password_hash("password123"),
            role=RoleEnum.EMPLOYEE.value,
            manager_id=priya.id,
            title=title,
        )
        db.add(u)
        ashoka_reports.append(u)
    db.flush()

    kavita = User(
        company_id=ashoka.id,
        name="Kavita Iyer",
        email="kavita@ashoka.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.HR.value,
        manager_id=None,
        title="HR Manager",
    )
    db.add(kavita)
    db.flush()

    # ── 3. Bright Path Consulting — flat hierarchy ─────────────────────────
    bright_path = Company(name="Bright Path Consulting")
    db.add(bright_path)
    db.flush()

    founder = User(
        company_id=bright_path.id,
        name="Arjun Kapoor",
        email="arjun@brightpath.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=None,
        title="Founder & CEO",
    )
    db.add(founder)
    db.flush()

    bp_specs = [
        ("Neha Gupta", "neha@brightpath.com", "Business Analyst"),
        ("Siddharth Jain", "siddharth@brightpath.com", "Consultant"),
        ("Ananya Bose", "ananya@brightpath.com", "Senior Consultant"),
        ("Rahul Desai", "rahul@brightpath.com", "Associate"),
        ("Tanvi Choudhury", "tanvi@brightpath.com", "Analyst"),
        ("Kunal Shah", "kunal@brightpath.com", "Senior Analyst"),
        ("Ishita Menon", "ishita@brightpath.com", "Consultant"),
        ("Divya Reddy", "divya@brightpath.com", "Junior Analyst"),
    ]
    bp_reports: list[User] = []
    for name, email, title in bp_specs:
        u = User(
            company_id=bright_path.id,
            name=name,
            email=email,
            hashed_password=get_password_hash("password123"),
            role=RoleEnum.EMPLOYEE.value,
            manager_id=founder.id,
            title=title,
        )
        db.add(u)
        bp_reports.append(u)
    db.flush()

    bp_hr = User(
        company_id=bright_path.id,
        name="Lakshmi Nair",
        email="hr@brightpath.com",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.HR.value,
        manager_id=None,
        title="People Operations",
    )
    db.add(bp_hr)
    db.flush()

    # ── 4. Feedback Cycles (3 months for each company) ─────────────────────
    cycle_months = [(5, 2026), (6, 2026), (7, 2026)]
    ashoka_cycles, bp_cycles = [], []
    for month, year in cycle_months:
        ac = FeedbackCycle(company_id=ashoka.id, month=month, year=year)
        bc = FeedbackCycle(company_id=bright_path.id, month=month, year=year)
        db.add(ac)
        db.add(bc)
        ashoka_cycles.append(ac)
        bp_cycles.append(bc)
    db.flush()

    # ── 5. Helper: create FeedbackScore rows ───────────────────────────────
    def make_scores(feedback: Feedback, score_values: list[int]) -> None:
        for param, score_val in zip(parameters, score_values):
            db.add(
                FeedbackScore(
                    feedback_id=feedback.id,
                    parameter_id=param.id,
                    score=score_val,
                    comment=f"Solid on {param.name.lower()} this cycle.",
                )
            )

    def make_feedback(
        cycle: FeedbackCycle,
        company: Company,
        giver: User,
        receiver: User,
        scores: list[int],
        submitted_on: datetime,
    ) -> Feedback:
        f = Feedback(
            cycle_id=cycle.id,
            company_id=company.id,
            given_by_id=giver.id,
            given_to_id=receiver.id,
            status=FeedbackStatusEnum.SUBMITTED.value,
            submitted_at=submitted_on,
        )
        db.add(f)
        db.flush()
        make_scores(f, scores)
        return f

    # ── 6. Ashoka — May 2026 (all submitted) ──────────────────────────────
    ac_may = ashoka_cycles[0]
    make_feedback(ac_may, ashoka, rohan, priya, [4, 5, 4, 4, 5], datetime(2026, 5, 28))
    may_scores = [
        [4, 4, 3, 5, 4],
        [5, 4, 4, 4, 5],
        [3, 4, 5, 4, 3],
        [4, 5, 4, 3, 4],
        [4, 4, 4, 4, 4],
        [5, 5, 3, 4, 5],
    ]
    for report, scores in zip(ashoka_reports, may_scores):
        make_feedback(ac_may, ashoka, priya, report, scores, datetime(2026, 5, 29))

    # ── 7. Ashoka — June 2026 (Rohan submitted; Priya missing Meena + Ravi) ─
    ac_jun = ashoka_cycles[1]
    make_feedback(ac_jun, ashoka, rohan, priya, [4, 4, 5, 4, 4], datetime(2026, 6, 27))

    # Priya submits for Aditya, Sneha, Vikram, Pooja (indices 0,1,2,5)
    submitted_reports = [ashoka_reports[0], ashoka_reports[1], ashoka_reports[2], ashoka_reports[5]]
    jun_scores = [[4, 3, 4, 5, 4], [5, 5, 4, 4, 5], [3, 3, 4, 4, 3], [4, 5, 5, 3, 4]]
    for report, scores in zip(submitted_reports, jun_scores):
        make_feedback(ac_jun, ashoka, priya, report, scores, datetime(2026, 6, 28))

    # Priya saves a DRAFT for Meena (index 3)
    draft = Feedback(
        cycle_id=ac_jun.id,
        company_id=ashoka.id,
        given_by_id=priya.id,
        given_to_id=ashoka_reports[3].id,
        status=FeedbackStatusEnum.DRAFT.value,
    )
    db.add(draft)
    db.flush()
    db.add(
        FeedbackScore(
            feedback_id=draft.id,
            parameter_id=parameters[0].id,
            score=3,
            comment="Still evaluating ownership this cycle.",
        )
    )
    # Ravi (index 4) has NO feedback record at all — fully pending.

    # ── 8. Ashoka — July 2026 (current — zero submissions, so HR catches both) ─
    # Intentionally left empty.

    # ── 9. Bright Path — May 2026 (all 8 submitted) ──────────────────────
    bp_may = bp_cycles[0]
    bp_may_scores = [
        [4, 5, 4, 4, 5], [5, 4, 3, 4, 4], [4, 4, 5, 4, 3],
        [3, 4, 4, 5, 4], [4, 5, 4, 4, 4], [5, 4, 4, 4, 5],
        [4, 3, 5, 4, 4], [4, 4, 4, 5, 3],
    ]
    for report, scores in zip(bp_reports, bp_may_scores):
        make_feedback(bp_may, bright_path, founder, report, scores, datetime(2026, 5, 30))

    # ── 10. Bright Path — June 2026 (founder submitted 5 of 8) ──────────
    bp_jun = bp_cycles[1]
    bp_jun_scores = [
        [5, 4, 4, 3, 5], [4, 5, 4, 4, 4], [3, 4, 5, 4, 4],
        [4, 4, 4, 5, 4], [5, 5, 4, 4, 3],
    ]
    for report, scores in zip(bp_reports[:5], bp_jun_scores):
        make_feedback(bp_jun, bright_path, founder, report, scores, datetime(2026, 6, 29))
    # bp_reports[5], [6], [7] are pending for June — and July has nothing at all.

    db.commit()
    print("[OK] Database seeded successfully!")
    print("     Ashoka Textiles : rohan@ashoka.com, priya@ashoka.com, kavita@ashoka.com")
    print("     Bright Path     : arjun@brightpath.com, hr@brightpath.com")
    print("     All passwords   : password123")
    print("     July 2026 cycle : no submissions -> HR dashboard shows pending for both companies")


if __name__ == "__main__":
    from app.db.session import SessionLocal

    _db = SessionLocal()
    try:
        seed_database(_db)
    finally:
        _db.close()
