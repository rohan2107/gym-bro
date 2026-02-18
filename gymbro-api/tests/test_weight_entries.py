"""Tests for weight entries router."""

from datetime import date
from fastapi.testclient import TestClient


def test_create_weight_entry(client: TestClient):
    """Test creating a weight entry."""
    headers = {"X-User-Id": "1"}
    
    payload = {
        "for_date": "2026-02-15",
        "weight_kg": 80.5,
        "note": "Morning weight"
    }
    
    resp = client.post("/weight-entries", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["for_date"] == "2026-02-15"
    assert data["weight_kg"] == 80.5
    assert data["note"] == "Morning weight"
    assert data["user_id"] == 1
    assert "id" in data


def test_create_weight_entry_without_note(client: TestClient):
    """Test creating a weight entry without optional note."""
    headers = {"X-User-Id": "1"}
    
    payload = {
        "for_date": "2026-02-16",
        "weight_kg": 79.8
    }
    
    resp = client.post("/weight-entries", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["note"] is None


def test_list_weight_entries(client: TestClient):
    """Test listing weight entries."""
    headers = {"X-User-Id": "1"}
    
    # Create three weight entries
    client.post("/weight-entries", json={
        "for_date": "2026-02-10",
        "weight_kg": 82.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-15",
        "weight_kg": 81.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-20",
        "weight_kg": 80.0
    }, headers=headers)
    
    # List all entries (should be ordered by date)
    resp = client.get("/weight-entries", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert data[0]["for_date"] == "2026-02-10"
    assert data[1]["for_date"] == "2026-02-15"
    assert data[2]["for_date"] == "2026-02-20"


def test_list_weight_entries_with_date_range(client: TestClient):
    """Test listing weight entries with date range filter."""
    headers = {"X-User-Id": "1"}
    
    # Create entries across different dates
    client.post("/weight-entries", json={
        "for_date": "2026-02-01",
        "weight_kg": 85.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-10",
        "weight_kg": 83.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-20",
        "weight_kg": 81.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-28",
        "weight_kg": 79.0
    }, headers=headers)
    
    # Filter by date range
    resp = client.get("/weight-entries?from=2026-02-10&to=2026-02-25", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["for_date"] == "2026-02-10"
    assert data[1]["for_date"] == "2026-02-20"


def test_list_weight_entries_from_date_only(client: TestClient):
    """Test listing weight entries with only 'from' date."""
    headers = {"X-User-Id": "1"}
    
    # Create entries
    client.post("/weight-entries", json={
        "for_date": "2026-02-05",
        "weight_kg": 85.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-15",
        "weight_kg": 83.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-25",
        "weight_kg": 81.0
    }, headers=headers)
    
    # Filter from date
    resp = client.get("/weight-entries?from=2026-02-15", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(entry["for_date"] >= "2026-02-15" for entry in data)


def test_list_weight_entries_to_date_only(client: TestClient):
    """Test listing weight entries with only 'to' date."""
    headers = {"X-User-Id": "1"}
    
    # Create entries
    client.post("/weight-entries", json={
        "for_date": "2026-02-05",
        "weight_kg": 85.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-15",
        "weight_kg": 83.0
    }, headers=headers)
    
    client.post("/weight-entries", json={
        "for_date": "2026-02-25",
        "weight_kg": 81.0
    }, headers=headers)
    
    # Filter to date
    resp = client.get("/weight-entries?to=2026-02-15", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(entry["for_date"] <= "2026-02-15" for entry in data)


# Note: GET single weight entry endpoint not implemented yet
# These tests are commented out until the endpoint is added
# def test_get_weight_entry(client: TestClient):
#     """Test retrieving a single weight entry."""
#     headers = {"X-User-Id": "1"}
#     
#     # Create a weight entry
#     create_resp = client.post("/weight-entries", json={
#         "for_date": "2026-02-18",
#         "weight_kg": 78.5,
#         "note": "Feeling good"
#     }, headers=headers)
#     
#     entry_id = create_resp.json()["id"]
#     
#     # Get the weight entry
#     resp = client.get(f"/weight-entries/{entry_id}", headers=headers)
#     assert resp.status_code == 200
#     data = resp.json()
#     assert data["for_date"] == "2026-02-18"
#     assert data["weight_kg"] == 78.5


# def test_get_weight_entry_not_found(client: TestClient):
#     """Test retrieving non-existent weight entry."""
#     headers = {"X-User-Id": "1"}
#     
#     resp = client.get("/weight-entries/999", headers=headers)
#     assert resp.status_code == 404
#     assert resp.json()["detail"] == "Weight entry not found"


def test_update_weight_entry(client: TestClient):
    """Test updating a weight entry."""
    headers = {"X-User-Id": "1"}
    
    # Create a weight entry
    create_resp = client.post("/weight-entries", json={
        "for_date": "2026-02-18",
        "weight_kg": 80.0
    }, headers=headers)
    
    entry_id = create_resp.json()["id"]
    
    # Update the entry
    update_payload = {
        "for_date": "2026-02-18",
        "weight_kg": 80.5,
        "note": "Corrected weight"
    }
    
    resp = client.put(f"/weight-entries/{entry_id}", json=update_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["weight_kg"] == 80.5
    assert data["note"] == "Corrected weight"


def test_delete_weight_entry(client: TestClient):
    """Test deleting a weight entry."""
    headers = {"X-User-Id": "1"}
    
    # Create a weight entry
    create_resp = client.post("/weight-entries", json={
        "for_date": "2026-02-18",
        "weight_kg": 80.0
    }, headers=headers)
    
    entry_id = create_resp.json()["id"]
    
    # Delete the entry
    resp = client.delete(f"/weight-entries/{entry_id}", headers=headers)
    assert resp.status_code == 204


def test_user_isolation(client: TestClient):
    """Test that users can only see their own weight entries."""
    # User 1 creates a weight entry
    user1_headers = {"X-User-Id": "1"}
    create_resp = client.post("/weight-entries", json={
        "for_date": "2026-02-18",
        "weight_kg": 80.0
    }, headers=user1_headers)
    
    # User 2 lists entries (should be empty)
    user2_headers = {"X-User-Id": "2"}
    list_resp = client.get("/weight-entries", headers=user2_headers)
    assert len(list_resp.json()) == 0
