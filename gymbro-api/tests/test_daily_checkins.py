from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import create_app
from app.db import get_session


@pytest.fixture()
def client():
    # Shared in-memory SQLite (single connection)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Import models BEFORE create_all (register tables)
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


def test_weight_entries(client: TestClient):
    headers = {"X-User-Id": "1"}
    today = date.today().isoformat()

    # Create weight entry
    resp = client.post(
        "/weight-entries",
        headers=headers,
        json={"for_date": today, "weight_kg": 75.5, "note": "morning"},
    )
    assert resp.status_code == 201
    entry = resp.json()
    assert entry["weight_kg"] == 75.5
    entry_id = entry["id"]

    # List weight entries
    list_resp = client.get("/weight-entries", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Update weight entry
    update_resp = client.put(
        f"/weight-entries/{entry_id}",
        headers=headers,
        json={"for_date": today, "weight_kg": 75.2, "note": "updated"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["weight_kg"] == 75.2

    # Delete weight entry
    del_resp = client.delete(f"/weight-entries/{entry_id}", headers=headers)
    assert del_resp.status_code == 204

    list_after = client.get("/weight-entries", headers=headers)
    assert len(list_after.json()) == 0


def test_workouts(client: TestClient):
    headers = {"X-User-Id": "1"}

    # Create workout
    resp = client.post(
        "/workouts",
        headers=headers,
        json={"name": "Chest Day", "note": "good session"},
    )
    assert resp.status_code == 201
    workout = resp.json()
    assert workout["name"] == "Chest Day"
    workout_id = workout["id"]

    # List workouts
    list_resp = client.get("/workouts", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Get single workout
    get_resp = client.get(f"/workouts/{workout_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Chest Day"

    # Update workout
    update_resp = client.put(
        f"/workouts/{workout_id}",
        headers=headers,
        json={"name": "Chest & Tri", "note": "updated"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Chest & Tri"

    # Delete workout
    del_resp = client.delete(f"/workouts/{workout_id}", headers=headers)
    assert del_resp.status_code == 204

    list_after = client.get("/workouts", headers=headers)
    assert len(list_after.json()) == 0


def test_exercise_sets(client: TestClient):
    headers = {"X-User-Id": "1"}

    # Create workout first
    workout_resp = client.post(
        "/workouts",
        headers=headers,
        json={"name": "Leg Day"},
    )
    workout_id = workout_resp.json()["id"]

    # Create exercise set
    resp = client.post(
        "/exercise-sets",
        headers=headers,
        json={
            "workout_id": workout_id,
            "exercise_name": "Squat",
            "reps": 8,
            "weight_kg": 100.0,
            "rpe": 9.0,
        },
    )
    assert resp.status_code == 201
    exercise = resp.json()
    assert exercise["exercise_name"] == "Squat"
    exercise_id = exercise["id"]

    # List exercise sets
    list_resp = client.get("/exercise-sets", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Update exercise set
    update_resp = client.put(
        f"/exercise-sets/{exercise_id}",
        headers=headers,
        json={
            "workout_id": workout_id,
            "exercise_name": "Squat",
            "reps": 10,
            "weight_kg": 100.0,
            "rpe": 8.0,
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["reps"] == 10

    # Delete exercise set
    del_resp = client.delete(f"/exercise-sets/{exercise_id}", headers=headers)
    assert del_resp.status_code == 204

    list_after = client.get("/exercise-sets", headers=headers)
    assert len(list_after.json()) == 0
