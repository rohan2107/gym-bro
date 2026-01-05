from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.db import get_session


@pytest.fixture()
def client():
    # 🔑 Shared in-memory SQLite (single connection)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 🔑 Import models BEFORE create_all (register tables)
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as c:
        yield c

    SQLModel.metadata.drop_all(engine)


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_daily_checkin_today_and_upsert(client: TestClient):
    headers = {"X-User-Id": "1"}

    # Today should return an empty shell when none exists
    resp = client.get("/daily-checkins/today", headers=headers)
    assert resp.status_code == 200

    today = date.today().isoformat()
    body = resp.json()

    assert body["checkin_date"] == today
    assert body["user_id"] == 1

    # Upsert today's check-in
    payload = {
        "weight": 75.2,
        "trained": True,
        "steps": 8000,
        "protein_met": True,
        "notes": "solid",
    }

    put_resp = client.put(
        f"/daily-checkins/{today}",
        json=payload,
        headers=headers,
    )
    assert put_resp.status_code == 200

    updated = put_resp.json()
    assert updated["weight"] == 75.2
    assert updated["trained"] is True
    assert updated["steps"] == 8000
    assert updated["protein_met"] is True
    assert updated["notes"] == "solid"

    # Range query should include the day
    list_resp = client.get(
        f"/daily-checkins?from={today}&to={today}",
        headers=headers,
    )
    assert list_resp.status_code == 200

    days = list_resp.json()
    assert len(days) == 1
    assert days[0]["checkin_date"] == today


def test_food_logs_are_user_scoped(client: TestClient):
    # Create a log for user 1
    resp = client.post(
        "/food-logs/",
        headers={"X-User-Id": "1"},
        json={"user_id": 1, "description": "Chicken bowl", "calories": 650},
    )
    assert resp.status_code == 201

    # User 1 sees it
    list_user1 = client.get("/food-logs/", headers={"X-User-Id": "1"})
    assert list_user1.status_code == 200
    assert len(list_user1.json()) == 1

    # User 2 should not see user 1's log
    list_user2 = client.get("/food-logs/", headers={"X-User-Id": "2"})
    assert list_user2.status_code == 200
    assert len(list_user2.json()) == 0
