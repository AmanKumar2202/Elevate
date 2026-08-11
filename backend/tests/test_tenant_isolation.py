"""
Tests that company A data is completely isolated from company B.
A Bright Path JWT must never be able to fetch Ashoka data, even by guessing IDs.
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


class TestTenantIsolation:
    def test_cycles_scoped_to_own_company(self, client, seeded_data):
        """Company B employee should only see Company B cycles."""
        data = seeded_data
        token = login(client, "emp1@beta.com")
        resp = client.get("/api/v1/feedback/cycles", headers=auth(token))
        assert resp.status_code == 200
        cycles = resp.json()
        returned_ids = {c["id"] for c in cycles}
        assert data["cycle_b"].id in returned_ids
        assert data["cycle_a"].id not in returned_ids

    def test_manager_cannot_submit_for_other_company_employee(self, client, seeded_data):
        """Manager A cannot give feedback to Company B employee."""
        data = seeded_data
        token = login(client, "manager@alpha.com")
        resp = client.post(
            "/api/v1/feedback/submit",
            json={
                "cycle_id": data["cycle_a"].id,
                "given_to_id": data["employee_b1"].id,
                "scores": [
                    {"parameter_id": p.id, "score": 4, "comment": "x"} for p in data["params"]
                ],
                "status": "SUBMITTED",
            },
            headers=auth(token),
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.json()}"

    def test_employee_cannot_read_other_company_feedback_by_id(self, client, seeded_data, db):
        """Company A employee cannot access Company B's feedback by guessing the ID."""
        data = seeded_data
        # Create a submitted feedback in Company B
        f = Feedback(
            cycle_id=data["cycle_b"].id,
            company_id=data["company_b"].id,
            given_by_id=data["manager_b"].id,
            given_to_id=data["employee_b1"].id,
            status="SUBMITTED",
            submitted_at=datetime.utcnow(),
        )
        db.add(f)
        db.flush()
        for p in data["params"]:
            db.add(FeedbackScore(feedback_id=f.id, parameter_id=p.id, score=4, comment="Good"))
        db.commit()

        token = login(client, "emp1@alpha.com")
        resp = client.get(f"/api/v1/feedback/received/{f.id}", headers=auth(token))
        assert resp.status_code in (403, 404)

    def test_hr_pending_scoped_to_own_company(self, client, seeded_data, db):
        """
        HR from Company A must not see Company B managers in the pending list.
        company_id is resolved from the authenticated user — not the query string.
        """
        data = seeded_data
        token = login(client, "hr@alpha.com")
        resp = client.get(
            f"/api/v1/hr/pending?cycle_id={data['cycle_a'].id}", headers=auth(token)
        )
        assert resp.status_code == 200
        manager_ids = {item["manager"]["id"] for item in resp.json()}
        assert data["manager_b"].id not in manager_ids

    def test_hr_cannot_access_other_company_cycle(self, client, seeded_data):
        """
        HR from Company A passing Company B's cycle_id.
        Managers returned are ALWAYS from company_a (JWT-derived company_id).
        The cycle_id only scopes the feedback lookup — since no cycle with that
        ID belongs to company_a, zero feedback rows are found, so ALL reports
        appear as pending. The manager list itself is NOT empty.
        This is correct behaviour: the guard is on managers (scoped by company_id),
        not on the cycle query param.
        """
        data = seeded_data
        token = login(client, "hr@alpha.com")
        resp = client.get(
            f"/api/v1/hr/pending?cycle_id={data['cycle_b'].id}", headers=auth(token)
        )
        assert resp.status_code == 404

    def test_non_hr_cannot_access_hr_endpoint(self, client, seeded_data):
        """EMPLOYEE role must receive 403 on HR endpoints."""
        token = login(client, "manager@alpha.com")
        resp = client.get(
            "/api/v1/hr/pending?cycle_id=1", headers=auth(token)
        )
        assert resp.status_code == 403

    def test_received_feedback_scoped_to_own_user(self, client, seeded_data, db):
        """
        Employee A1's received feedback must not include feedback submitted to A2.
        """
        data = seeded_data
        # Submit feedback for employee_a2
        f = Feedback(
            cycle_id=data["cycle_a"].id,
            company_id=data["company_a"].id,
            given_by_id=data["manager_a"].id,
            given_to_id=data["employee_a2"].id,
            status="SUBMITTED",
            submitted_at=datetime.utcnow(),
        )
        db.add(f)
        db.flush()
        for p in data["params"]:
            db.add(FeedbackScore(feedback_id=f.id, parameter_id=p.id, score=3, comment="OK"))
        db.commit()

        token = login(client, "emp1@alpha.com")
        resp = client.get("/api/v1/feedback/received", headers=auth(token))
        assert resp.status_code == 200
        assert len(resp.json()) == 0  # emp1 has received nothing
