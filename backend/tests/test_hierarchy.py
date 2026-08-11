"""
Tests that the self-referencing manager_id hierarchy works correctly for:
  - Ashoka-style: 3-level chain (manager_a → middle_manager → report_of_middle)
  - Bright Path-style: flat (manager_b → employee_b1 directly)
  - Priya-like: a user who both gives AND receives feedback
"""
import pytest
from app.models.models import Feedback, FeedbackScore
from datetime import datetime


def login(client, email: str, password: str = "password") -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestOrgHierarchy:
    def test_top_manager_sees_only_direct_reports(self, client, seeded_data):
        """
        Manager A has: employee_a1, employee_a2, middle_manager as direct reports.
        Should NOT see report_of_middle (grandchild).
        """
        data = seeded_data
        token = login(client, "manager@alpha.com")
        resp = client.get("/api/v1/users/my-reports", headers=auth(token))
        assert resp.status_code == 200
        ids = {r["id"] for r in resp.json()}

        assert data["employee_a1"].id in ids
        assert data["employee_a2"].id in ids
        assert data["middle_manager"].id in ids
        # grandchild must not be visible
        assert data["report_of_middle"].id not in ids

    def test_middle_manager_sees_only_own_reports(self, client, seeded_data):
        """
        Middle manager has only report_of_middle.
        Should NOT see employee_a1 or employee_a2 (siblings, not reports).
        """
        data = seeded_data
        token = login(client, "mid@alpha.com")
        resp = client.get("/api/v1/users/my-reports", headers=auth(token))
        assert resp.status_code == 200
        ids = {r["id"] for r in resp.json()}

        assert data["report_of_middle"].id in ids
        assert data["employee_a1"].id not in ids
        assert data["employee_a2"].id not in ids

    def test_flat_org_founder_sees_all_direct_reports(self, client, seeded_data):
        """Flat org: manager_b's single direct report is employee_b1."""
        data = seeded_data
        token = login(client, "manager@beta.com")
        resp = client.get("/api/v1/users/my-reports", headers=auth(token))
        assert resp.status_code == 200
        ids = {r["id"] for r in resp.json()}
        assert data["employee_b1"].id in ids

    def test_leaf_employee_has_no_reports(self, client, seeded_data):
        """A leaf employee should have an empty reports list."""
        token = login(client, "emp1@alpha.com")
        resp = client.get("/api/v1/users/my-reports", headers=auth(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_middle_manager_can_give_and_receive_feedback(self, client, seeded_data, db):
        """
        Mirrors the Priya scenario:
          - Middle manager RECEIVES feedback from manager_a (upward).
          - Middle manager GIVES feedback to report_of_middle (downward).
        No special-casing — same User entity.
        """
        data = seeded_data

        # Manager A gives feedback to middle_manager (middle manager receives)
        f_received = Feedback(
            cycle_id=data["cycle_a"].id,
            company_id=data["company_a"].id,
            given_by_id=data["manager_a"].id,
            given_to_id=data["middle_manager"].id,
            status="SUBMITTED",
            submitted_at=datetime.utcnow(),
        )
        db.add(f_received)
        db.flush()
        for p in data["params"]:
            db.add(
                FeedbackScore(
                    feedback_id=f_received.id,
                    parameter_id=p.id,
                    score=4,
                    comment="Good",
                )
            )
        db.commit()

        # Middle manager gives feedback to their own report
        token = login(client, "mid@alpha.com")
        give_resp = client.post(
            "/api/v1/feedback/submit",
            json={
                "cycle_id": data["cycle_a"].id,
                "given_to_id": data["report_of_middle"].id,
                "scores": [
                    {"parameter_id": p.id, "score": 4, "comment": "Nice"} for p in data["params"]
                ],
                "status": "SUBMITTED",
            },
            headers=auth(token),
        )
        assert give_resp.status_code == 200, give_resp.json()

        # Middle manager also receives their own feedback
        receive_resp = client.get("/api/v1/feedback/received", headers=auth(token))
        assert receive_resp.status_code == 200
        received = receive_resp.json()
        assert len(received) == 1
        assert received[0]["given_by_name"] == "Manager A"
        assert len(received[0]["scores"]) == 5

    def test_hr_is_not_in_reporting_hierarchy(self, client, seeded_data):
        """
        HR user (hr_a) should have zero direct reports — their role is orthogonal
        to the manager_id hierarchy.
        """
        token = login(client, "hr@alpha.com")
        resp = client.get("/api/v1/users/my-reports", headers=auth(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_three_level_submission_status_per_level(self, client, seeded_data):
        """
        HR pending query should show separate entries for manager_a and middle_manager
        because they each have their own direct reports.
        """
        data = seeded_data
        token = login(client, "hr@alpha.com")
        resp = client.get(
            f"/api/v1/hr/pending?cycle_id={data['cycle_a'].id}", headers=auth(token)
        )
        assert resp.status_code == 200
        managers = {item["manager"]["id"] for item in resp.json()}
        # Both levels should appear
        assert data["manager_a"].id in managers
        assert data["middle_manager"].id in managers
