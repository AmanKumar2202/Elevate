"""Tests for the core give-feedback and receive-feedback flows."""
import pytest
from app.models.models import Feedback, FeedbackScore, FeedbackStatusEnum
from datetime import datetime, timezone


def login(client, email: str, password: str = "password") -> str:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAuthFlow:
    def test_login_success(self, client, seeded_data):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "manager@alpha.com", "password": "password"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "manager@alpha.com"
        assert data["user"]["role"] == "EMPLOYEE"

    def test_login_wrong_password(self, client, seeded_data):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "manager@alpha.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client, seeded_data):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@nowhere.com", "password": "password"},
        )
        assert resp.status_code == 401

    def test_protected_route_without_token(self, client, seeded_data):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401


class TestManagerFeedbackFlow:
    def test_submit_feedback_to_direct_report(self, client, seeded_data):
        data = seeded_data
        token = login(client, "manager@alpha.com")
        payload = {
            "cycle_id": data["cycle_a"].id,
            "given_to_id": data["employee_a1"].id,
            "scores": [
                {"parameter_id": p.id, "score": 4, "comment": "Good work"}
                for p in data["params"]
            ],
            "status": "SUBMITTED",
        }
        resp = client.post("/api/v1/feedback/submit", json=payload, headers=auth(token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "SUBMITTED"

    def test_cannot_submit_to_non_report(self, client, seeded_data):
        """Manager A cannot submit feedback for Company B employee."""
        data = seeded_data
        token = login(client, "manager@alpha.com")
        payload = {
            "cycle_id": data["cycle_a"].id,
            "given_to_id": data["employee_b1"].id,
            "scores": [
                {"parameter_id": p.id, "score": 3, "comment": "x"} for p in data["params"]
            ],
            "status": "SUBMITTED",
        }
        resp = client.post("/api/v1/feedback/submit", json=payload, headers=auth(token))
        assert resp.status_code == 403

    def test_save_as_draft(self, client, seeded_data):
        data = seeded_data
        token = login(client, "manager@alpha.com")
        payload = {
            "cycle_id": data["cycle_a"].id,
            "given_to_id": data["employee_a1"].id,
            "scores": [
                {"parameter_id": p.id, "score": 3, "comment": "Partial"} for p in data["params"]
            ],
            "status": "DRAFT",
        }
        resp = client.post("/api/v1/feedback/submit", json=payload, headers=auth(token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "DRAFT"

    def test_cannot_modify_submitted_feedback(self, client, seeded_data, db):
        data = seeded_data
        # First submit
        token = login(client, "manager@alpha.com")
        payload = {
            "cycle_id": data["cycle_a"].id,
            "given_to_id": data["employee_a1"].id,
            "scores": [
                {"parameter_id": p.id, "score": 5, "comment": "Excellent"} for p in data["params"]
            ],
            "status": "SUBMITTED",
        }
        resp = client.post("/api/v1/feedback/submit", json=payload, headers=auth(token))
        assert resp.status_code == 200

        # Attempt to modify
        resp2 = client.post("/api/v1/feedback/submit", json=payload, headers=auth(token))
        assert resp2.status_code == 400

    def test_score_out_of_range_rejected(self, client, seeded_data):
        data = seeded_data
        token = login(client, "manager@alpha.com")
        payload = {
            "cycle_id": data["cycle_a"].id,
            "given_to_id": data["employee_a1"].id,
            "scores": [
                {"parameter_id": data["params"][0].id, "score": 6, "comment": "Too high"}
            ],
            "status": "SUBMITTED",
        }
        resp = client.post("/api/v1/feedback/submit", json=payload, headers=auth(token))
        assert resp.status_code == 422  # Pydantic validation error

    def test_my_submissions_includes_pending(self, client, seeded_data):
        """Submission list should include PENDING employees (zero feedback rows)."""
        data = seeded_data
        token = login(client, "manager@alpha.com")
        resp = client.get(
            f"/api/v1/feedback/my-submissions?cycle_id={data['cycle_a'].id}",
            headers=auth(token),
        )
        assert resp.status_code == 200
        statuses = resp.json()
        assert any(s["status"] == "PENDING" for s in statuses)

    def test_cannot_query_submission_status_for_other_company_cycle(self, client, seeded_data):
        token = login(client, "manager@alpha.com")
        resp = client.get(
            f"/api/v1/feedback/my-submissions?cycle_id={seeded_data['cycle_b'].id}",
            headers=auth(token),
        )
        assert resp.status_code == 404

    def test_submitted_feedback_requires_all_fixed_parameters(self, client, seeded_data):
        data = seeded_data
        token = login(client, "manager@alpha.com")
        resp = client.post(
            "/api/v1/feedback/submit",
            json={
                "cycle_id": data["cycle_a"].id,
                "given_to_id": data["employee_a1"].id,
                "scores": [{"parameter_id": data["params"][0].id, "score": 4, "comment": "Good work"}],
                "status": "SUBMITTED",
            },
            headers=auth(token),
        )
        assert resp.status_code == 400

    def test_draft_can_be_saved_without_all_parameters(self, client, seeded_data):
        data = seeded_data
        token = login(client, "manager@alpha.com")
        resp = client.post(
            "/api/v1/feedback/submit",
            json={
                "cycle_id": data["cycle_a"].id,
                "given_to_id": data["employee_a1"].id,
                "scores": [{"parameter_id": data["params"][0].id, "score": 4, "comment": "Initial note"}],
                "status": "DRAFT",
            },
            headers=auth(token),
        )
        assert resp.status_code == 200
        statuses = client.get(
            f"/api/v1/feedback/my-submissions?cycle_id={data['cycle_a'].id}",
            headers=auth(token),
        ).json()
        draft = next(item for item in statuses if item["employee"]["id"] == data["employee_a1"].id)
        assert draft["scores"] == [{"parameter_id": data["params"][0].id, "score": 4, "comment": "Initial note"}]

    def test_unknown_feedback_status_is_rejected(self, client, seeded_data):
        data = seeded_data
        token = login(client, "manager@alpha.com")
        resp = client.post(
            "/api/v1/feedback/submit",
            json={"cycle_id": data["cycle_a"].id, "given_to_id": data["employee_a1"].id, "scores": [], "status": "APPROVED"},
            headers=auth(token),
        )
        assert resp.status_code == 422


class TestEmployeeFeedbackView:
    def test_employee_sees_received_feedback(self, client, seeded_data, db):
        data = seeded_data
        # Create submitted feedback
        f = Feedback(
            cycle_id=data["cycle_a"].id,
            company_id=data["company_a"].id,
            given_by_id=data["manager_a"].id,
            given_to_id=data["employee_a1"].id,
            status="SUBMITTED",
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(f)
        db.flush()
        for p in data["params"]:
            db.add(FeedbackScore(feedback_id=f.id, parameter_id=p.id, score=4, comment="Great"))
        db.commit()

        token = login(client, "emp1@alpha.com")
        resp = client.get("/api/v1/feedback/received", headers=auth(token))
        assert resp.status_code == 200
        received = resp.json()
        assert len(received) == 1
        assert len(received[0]["scores"]) == 5

    def test_draft_feedback_not_visible_to_employee(self, client, seeded_data, db):
        data = seeded_data
        f = Feedback(
            cycle_id=data["cycle_a"].id,
            company_id=data["company_a"].id,
            given_by_id=data["manager_a"].id,
            given_to_id=data["employee_a1"].id,
            status="DRAFT",
        )
        db.add(f)
        db.commit()

        token = login(client, "emp1@alpha.com")
        resp = client.get("/api/v1/feedback/received", headers=auth(token))
        assert resp.status_code == 200
        assert len(resp.json()) == 0  # Draft not visible

