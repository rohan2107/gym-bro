"""Tests for daily check-ins router."""

from datetime import date
from fastapi.testclient import TestClient


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


def test_get_today_checkin_returns_template_when_not_exists(client: TestClient):
    """Test that /today returns non-persisted template when no check-in exists."""
    headers = {"X-User-Id": "999"}  # Fresh user with no check-ins
    
    resp = client.get("/daily-checkins/today", headers=headers)
    assert resp.status_code == 200
    
    body = resp.json()
    # Template should have all default values
    assert body["id"] is None  # Not persisted yet
    assert body["user_id"] == 999
    assert body["checkin_date"] == date.today().isoformat()
    assert body["weight"] is None
    assert body["trained"] is False
    assert body["steps"] is None
    assert body["protein_met"] is False
    assert body["notes"] is None
    assert "created_at" in body
    assert "updated_at" in body


def test_get_checkin_by_date_returns_template_when_not_exists(client: TestClient):
    """Test that /{date} returns non-persisted template when no check-in exists."""
    headers = {"X-User-Id": "1"}
    past_date = "2026-01-15"
    
    resp = client.get(f"/daily-checkins/{past_date}", headers=headers)
    assert resp.status_code == 200
    
    body = resp.json()
    # Template should have all default values
    assert body["id"] is None  # Not persisted yet
    assert body["user_id"] == 1
    assert body["checkin_date"] == past_date
    assert body["weight"] is None
    assert body["trained"] is False


def test_upsert_creates_new_checkin_when_not_exists(client: TestClient):
    """Test PUT creates new check-in (INSERT path) when none exists."""
    headers = {"X-User-Id": "1"}
    past_date = "2026-01-10"
    
    # Verify no check-in exists (should get template)
    get_resp = client.get(f"/daily-checkins/{past_date}", headers=headers)
    assert get_resp.json()["id"] is None  # Template, not persisted
    
    # Create new check-in via PUT (INSERT path)
    payload = {
        "weight": 80.5,
        "trained": True,
        "steps": 12000,
        "protein_met": True,
        "notes": "Great day"
    }
    put_resp = client.put(
        f"/daily-checkins/{past_date}",
        json=payload,
        headers=headers
    )
    
    assert put_resp.status_code == 200
    created = put_resp.json()
    assert created["id"] is not None  # Now persisted
    assert created["checkin_date"] == past_date
    assert created["weight"] == 80.5
    assert created["trained"] is True
    assert created["steps"] == 12000
    assert created["protein_met"] is True
    assert created["notes"] == "Great day"
    
    # Verify it's actually persisted
    get_again = client.get(f"/daily-checkins/{past_date}", headers=headers)
    assert get_again.json()["id"] == created["id"]


def test_upsert_with_partial_data(client: TestClient):
    """Test PUT with partial data (some fields null)."""
    headers = {"X-User-Id": "1"}
    test_date = "2026-01-20"
    
    # Create with only some fields
    payload = {
        "weight": 78.0,
        "trained": False,
        # steps, protein_met, notes intentionally omitted
    }
    
    resp = client.put(
        f"/daily-checkins/{test_date}",
        json=payload,
        headers=headers
    )
    
    assert resp.status_code == 200
    body = resp.json()
    assert body["weight"] == 78.0
    assert body["trained"] is False
    assert body["steps"] is None
    assert body["protein_met"] is False
    assert body["notes"] is None


def test_list_daily_checkins_with_date_range(client: TestClient):
    """Test listing check-ins with from/to date filters."""
    headers = {"X-User-Id": "1"}
    
    # Create multiple check-ins
    dates = ["2026-02-01", "2026-02-05", "2026-02-10", "2026-02-15"]
    for d in dates:
        client.put(
            f"/daily-checkins/{d}",
            json={"weight": 75.0, "trained": True},
            headers=headers
        )
    
    # Test from filter
    resp = client.get("/daily-checkins?from=2026-02-05", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 3  # Should include 02-05, 02-10, 02-15 (and possibly today)
    assert all(r["checkin_date"] >= "2026-02-05" for r in results)
    
    # Test to filter
    resp = client.get("/daily-checkins?to=2026-02-10", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert all(r["checkin_date"] <= "2026-02-10" for r in results)
    
    # Test from and to together
    resp = client.get("/daily-checkins?from=2026-02-05&to=2026-02-10", headers=headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 2  # Should be exactly 02-05 and 02-10
    assert results[0]["checkin_date"] == "2026-02-05"
    assert results[1]["checkin_date"] == "2026-02-10"


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
