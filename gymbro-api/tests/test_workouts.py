"""Tests for workouts router."""

from fastapi.testclient import TestClient


def test_create_workout(client: TestClient):
    """Test creating a workout."""
    headers = {"X-User-Id": "1"}
    
    payload = {
        "name": "Push Day",
        "note": "Chest and triceps"
    }
    
    resp = client.post("/workouts", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Push Day"
    assert data["note"] == "Chest and triceps"
    assert data["user_id"] == 1
    assert "id" in data
    assert "started_at" in data


def test_create_workout_without_note(client: TestClient):
    """Test creating a workout without optional note."""
    headers = {"X-User-Id": "1"}
    
    payload = {
        "name": "Leg Day"
    }
    
    resp = client.post("/workouts", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Leg Day"
    assert data["note"] is None


def test_list_workouts(client: TestClient):
    """Test listing workouts."""
    headers = {"X-User-Id": "1"}
    
    # Create two workouts
    client.post("/workouts", json={"name": "Pull Day"}, headers=headers)
    client.post("/workouts", json={"name": "Cardio"}, headers=headers)
    
    # List all workouts
    resp = client.get("/workouts", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Should be ordered by started_at desc (most recent first)
    assert data[0]["name"] == "Cardio"
    assert data[1]["name"] == "Pull Day"


def test_get_workout(client: TestClient):
    """Test retrieving a single workout."""
    headers = {"X-User-Id": "1"}
    
    # Create a workout
    create_resp = client.post("/workouts", json={
        "name": "Upper Body",
        "note": "Back and shoulders"
    }, headers=headers)
    
    workout_id = create_resp.json()["id"]
    
    # Get the workout
    resp = client.get(f"/workouts/{workout_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Upper Body"
    assert data["note"] == "Back and shoulders"


def test_get_workout_not_found(client: TestClient):
    """Test retrieving non-existent workout."""
    headers = {"X-User-Id": "1"}
    
    resp = client.get("/workouts/999", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Workout not found."


def test_update_workout(client: TestClient):
    """Test updating a workout."""
    headers = {"X-User-Id": "1"}
    
    # Create a workout
    create_resp = client.post("/workouts", json={
        "name": "Morning Workout"
    }, headers=headers)
    
    workout_id = create_resp.json()["id"]
    
    # Update the workout
    update_payload = {
        "name": "Morning Strength",
        "note": "Added accessory work"
    }
    
    resp = client.put(f"/workouts/{workout_id}", json=update_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Morning Strength"
    assert data["note"] == "Added accessory work"


def test_update_workout_not_found(client: TestClient):
    """Test updating non-existent workout."""
    headers = {"X-User-Id": "1"}
    
    update_payload = {
        "name": "Not found"
    }
    
    resp = client.put("/workouts/999", json=update_payload, headers=headers)
    assert resp.status_code == 404


def test_delete_workout(client: TestClient):
    """Test deleting a workout."""
    headers = {"X-User-Id": "1"}
    
    # Create a workout
    create_resp = client.post("/workouts", json={
        "name": "Test Workout"
    }, headers=headers)
    
    workout_id = create_resp.json()["id"]
    
    # Delete the workout
    resp = client.delete(f"/workouts/{workout_id}", headers=headers)
    assert resp.status_code == 204
    
    # Verify it's deleted
    get_resp = client.get(f"/workouts/{workout_id}", headers=headers)
    assert get_resp.status_code == 404


def test_user_isolation(client: TestClient):
    """Test that users can only see their own workouts."""
    # User 1 creates a workout
    user1_headers = {"X-User-Id": "1"}
    create_resp = client.post("/workouts", json={
        "name": "User 1 workout"
    }, headers=user1_headers)
    workout_id = create_resp.json()["id"]
    
    # User 2 tries to access user 1's workout
    user2_headers = {"X-User-Id": "2"}
    resp = client.get(f"/workouts/{workout_id}", headers=user2_headers)
    assert resp.status_code == 404
    
    # User 2 lists workouts (should be empty)
    list_resp = client.get("/workouts", headers=user2_headers)
    assert len(list_resp.json()) == 0


def test_user_cannot_update_other_users_workout(client: TestClient):
    """Test that users cannot update other users' workouts."""
    # User 1 creates a workout
    user1_headers = {"X-User-Id": "1"}
    create_resp = client.post("/workouts", json={
        "name": "User 1 workout"
    }, headers=user1_headers)
    workout_id = create_resp.json()["id"]
    
    # User 2 tries to update user 1's workout
    user2_headers = {"X-User-Id": "2"}
    resp = client.put(f"/workouts/{workout_id}", json={
        "name": "Hacked"
    }, headers=user2_headers)
    assert resp.status_code == 404


def test_user_cannot_delete_other_users_workout(client: TestClient):
    """Test that users cannot delete other users' workouts."""
    # User 1 creates a workout
    user1_headers = {"X-User-Id": "1"}
    create_resp = client.post("/workouts", json={
        "name": "User 1 workout"
    }, headers=user1_headers)
    workout_id = create_resp.json()["id"]
    
    # User 2 tries to delete user 1's workout
    user2_headers = {"X-User-Id": "2"}
    resp = client.delete(f"/workouts/{workout_id}", headers=user2_headers)
    assert resp.status_code == 404
    
    # Verify workout still exists for user 1
    get_resp = client.get(f"/workouts/{workout_id}", headers=user1_headers)
    assert get_resp.status_code == 200
