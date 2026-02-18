"""Tests for food logs router."""

from fastapi.testclient import TestClient


def test_create_food_log(client: TestClient):
    """Test creating a food log."""
    headers = {"X-User-Id": "1"}
    
    payload = {
        "description": "Chicken breast",
        "calories": 200,
        "protein_g": 40,
        "carbs_g": 0,
        "fat_g": 5
    }
    
    resp = client.post("/food-logs/", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Chicken breast"
    assert data["calories"] == 200
    assert data["protein_g"] == 40
    assert data["user_id"] == 1
    assert "id" in data
    assert "logged_at" in data


def test_list_food_logs(client: TestClient):
    """Test listing food logs."""
    headers = {"X-User-Id": "1"}
    
    # Create two food logs
    client.post("/food-logs/", json={
        "description": "Oatmeal",
        "calories": 150,
        "protein_g": 5,
        "carbs_g": 27,
        "fat_g": 3
    }, headers=headers)
    
    client.post("/food-logs/", json={
        "description": "Apple",
        "calories": 95,
        "protein_g": 0,
        "carbs_g": 25,
        "fat_g": 0
    }, headers=headers)
    
    # List all logs
    resp = client.get("/food-logs/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["description"] == "Oatmeal"
    assert data[1]["description"] == "Apple"


def test_get_food_log(client: TestClient):
    """Test retrieving a single food log."""
    headers = {"X-User-Id": "1"}
    
    # Create a food log
    create_resp = client.post("/food-logs/", json={
        "description": "Salmon",
        "calories": 300,
        "protein_g": 35,
        "carbs_g": 0,
        "fat_g": 17
    }, headers=headers)
    
    log_id = create_resp.json()["id"]
    
    # Get the food log
    resp = client.get(f"/food-logs/{log_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Salmon"
    assert data["calories"] == 300


def test_get_food_log_not_found(client: TestClient):
    """Test retrieving non-existent food log."""
    headers = {"X-User-Id": "1"}
    
    resp = client.get("/food-logs/999", headers=headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Food log not found"


def test_update_food_log(client: TestClient):
    """Test updating a food log."""
    headers = {"X-User-Id": "1"}
    
    # Create a food log
    create_resp = client.post("/food-logs/", json={
        "description": "Rice",
        "calories": 200,
        "protein_g": 4,
        "carbs_g": 45,
        "fat_g": 1
    }, headers=headers)
    
    log_id = create_resp.json()["id"]
    
    # Update the food log
    update_payload = {
        "description": "Brown Rice",
        "calories": 220,
        "protein_g": 5,
        "carbs_g": 46,
        "fat_g": 2
    }
    
    resp = client.put(f"/food-logs/{log_id}", json=update_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Brown Rice"
    assert data["calories"] == 220
    assert data["protein_g"] == 5


def test_update_food_log_not_found(client: TestClient):
    """Test updating non-existent food log."""
    headers = {"X-User-Id": "1"}
    
    update_payload = {
        "description": "Not found",
        "calories": 100
    }
    
    resp = client.put("/food-logs/999", json=update_payload, headers=headers)
    assert resp.status_code == 404


def test_delete_food_log(client: TestClient):
    """Test deleting a food log."""
    headers = {"X-User-Id": "1"}
    
    # Create a food log
    create_resp = client.post("/food-logs/", json={
        "description": "Pizza",
        "calories": 800,
        "protein_g": 30,
        "carbs_g": 90,
        "fat_g": 35
    }, headers=headers)
    
    log_id = create_resp.json()["id"]
    
    # Delete the food log
    resp = client.delete(f"/food-logs/{log_id}", headers=headers)
    assert resp.status_code == 204
    
    # Verify it's deleted
    get_resp = client.get(f"/food-logs/{log_id}", headers=headers)
    assert get_resp.status_code == 404


def test_user_isolation(client: TestClient):
    """Test that users can only see their own food logs."""
    # User 1 creates a food log
    user1_headers = {"X-User-Id": "1"}
    create_resp = client.post("/food-logs/", json={
        "description": "User 1 meal",
        "calories": 500
    }, headers=user1_headers)
    log_id = create_resp.json()["id"]
    
    # User 2 tries to access user 1's food log
    user2_headers = {"X-User-Id": "2"}
    resp = client.get(f"/food-logs/{log_id}", headers=user2_headers)
    assert resp.status_code == 404
    
    # User 2 lists food logs (should be empty)
    list_resp = client.get("/food-logs/", headers=user2_headers)
    assert len(list_resp.json()) == 0


def test_create_food_log_with_optional_fields(client: TestClient):
    """Test creating a food log with only required fields."""
    headers = {"X-User-Id": "1"}
    
    payload = {
        "description": "Snack"
    }
    
    resp = client.post("/food-logs/", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Snack"
    assert data["calories"] is None
    assert data["protein_g"] is None
