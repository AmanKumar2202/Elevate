"""
Test fixtures — SQLite in-memory for speed and isolation.
Uses native_enum=False (varchar storage) so SQLite handles the role/status columns.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.models import Base, Company, User, FeedbackParameter, FeedbackCycle, RoleEnum
from app.core.deps import get_db
from app.core.security import get_password_hash

SQLALCHEMY_TEST_URL = "sqlite:///./test_performance.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seeded_data(db):
    """Seed minimal data for both companies to cover all test scenarios."""

    # 5 global parameters
    params = [
        FeedbackParameter(name="Ownership", description="Ownership"),
        FeedbackParameter(name="Communication", description="Communication"),
        FeedbackParameter(name="Quality of Work", description="Quality of Work"),
        FeedbackParameter(name="Problem Solving", description="Problem Solving"),
        FeedbackParameter(name="Collaboration", description="Collaboration"),
    ]
    db.add_all(params)
    db.flush()

    # Company A — 3-level hierarchy (mirrors Ashoka Textiles)
    company_a = Company(name="Company Alpha")
    company_b = Company(name="Company Beta")
    db.add_all([company_a, company_b])
    db.flush()

    # Level 1 — top manager (no manager_id)
    manager_a = User(
        company_id=company_a.id,
        name="Manager A",
        email="manager@alpha.com",
        hashed_password=get_password_hash("password"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=None,
    )
    db.add(manager_a)
    db.flush()

    # Level 2 — middle manager (reports to manager_a, has own reports)
    middle_manager = User(
        company_id=company_a.id,
        name="Middle Manager",
        email="mid@alpha.com",
        hashed_password=get_password_hash("password"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=manager_a.id,
    )
    db.add(middle_manager)
    db.flush()

    # Direct reports of manager_a (not under middle_manager)
    employee_a1 = User(
        company_id=company_a.id,
        name="Employee A1",
        email="emp1@alpha.com",
        hashed_password=get_password_hash("password"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=manager_a.id,
    )
    employee_a2 = User(
        company_id=company_a.id,
        name="Employee A2",
        email="emp2@alpha.com",
        hashed_password=get_password_hash("password"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=manager_a.id,
    )
    db.add_all([employee_a1, employee_a2])
    db.flush()

    # Level 3 — reports to middle_manager
    report_of_middle = User(
        company_id=company_a.id,
        name="Report Of Middle",
        email="report_mid@alpha.com",
        hashed_password=get_password_hash("password"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=middle_manager.id,
    )
    db.add(report_of_middle)
    db.flush()

    # HR user for Company A
    hr_a = User(
        company_id=company_a.id,
        name="HR Alpha",
        email="hr@alpha.com",
        hashed_password=get_password_hash("password"),
        role=RoleEnum.HR.value,
        manager_id=None,
    )
    db.add(hr_a)
    db.flush()

    # Company B — flat hierarchy (mirrors Bright Path)
    manager_b = User(
        company_id=company_b.id,
        name="Manager B",
        email="manager@beta.com",
        hashed_password=get_password_hash("password"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=None,
    )
    db.add(manager_b)
    db.flush()

    employee_b1 = User(
        company_id=company_b.id,
        name="Employee B1",
        email="emp1@beta.com",
        hashed_password=get_password_hash("password"),
        role=RoleEnum.EMPLOYEE.value,
        manager_id=manager_b.id,
    )
    db.add(employee_b1)
    db.flush()

    # Cycles
    cycle_a = FeedbackCycle(company_id=company_a.id, month=7, year=2026)
    cycle_b = FeedbackCycle(company_id=company_b.id, month=7, year=2026)
    db.add_all([cycle_a, cycle_b])
    db.commit()

    return {
        "params": params,
        "company_a": company_a,
        "company_b": company_b,
        "manager_a": manager_a,
        "middle_manager": middle_manager,
        "employee_a1": employee_a1,
        "employee_a2": employee_a2,
        "report_of_middle": report_of_middle,
        "hr_a": hr_a,
        "manager_b": manager_b,
        "employee_b1": employee_b1,
        "cycle_a": cycle_a,
        "cycle_b": cycle_b,
    }
