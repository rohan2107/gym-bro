"""Tests for photo meal logging endpoint."""

import pytest
from io import BytesIO
from PIL import Image
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
from app.models import User


@pytest.fixture
def valid_image_file():
    """Create a valid test image file."""
    image = Image.new('RGB', (500, 500), color='red')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return ("test_meal.jpg", buffer, "image/jpeg")


@pytest.fixture
def small_image_file():
    """Create an image that's too small."""
    image = Image.new('RGB', (100, 100), color='blue')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return ("small.jpg", buffer, "image/jpeg")


@pytest.fixture
def mock_vision_predictions():
    """Mock Vision API predictions."""
    return [
        {
            "label": "pizza",
            "confidence": 0.85,
            "source": "mock_development"
        }
    ]


@pytest.fixture
def mock_nutrition_data():
    """Mock USDA nutrition data."""
    return {
        "name": "Pizza, cheese, regular crust",
        "fdc_id": 174987,
        "calories": 265,
        "protein_g": 11.0,
        "carbs_g": 33.0,
        "fat_g": 10.0,
        "serving_size": "100g",
        "confidence": "high"
    }


class TestPhotoMealLogging:
    """Test suite for photo meal logging endpoint."""

    def test_upload_photo_success(
        self, 
        client: TestClient, 
        user_token: str,
        test_user_in_db,
        valid_image_file,
        mock_vision_predictions,
        mock_nutrition_data
    ):
        """Test successful photo upload and food detection."""
        # Mock the nutrition service to return data
        with patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_nutrition_data
            
            # Upload photo
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "predictions" in data
        assert "rate_limit" in data
        assert "image_info" in data
        
        # Check predictions
        assert len(data["predictions"]) > 0
        prediction = data["predictions"][0]
        assert "label" in prediction
        assert "confidence" in prediction
        assert "nutrition" in prediction
        
        # Check nutrition data
        nutrition = prediction["nutrition"]
        assert nutrition["name"] == "Pizza, cheese, regular crust"
        assert nutrition["calories"] == 265
        assert nutrition["protein_g"] == 11.0
        
        # Check rate limit
        assert data["rate_limit"]["remaining"] < 30  # Should be decremented
        assert data["rate_limit"]["limit"] == 30

    def test_upload_photo_invalid_image(
        self,
        client: TestClient,
        user_token: str
    ):
        """Test upload with invalid image data."""
        invalid_file = ("test.txt", BytesIO(b"not an image"), "text/plain")
        
        response = client.post(
            "/food-logs/from-photo",
            files={"photo": invalid_file},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_upload_photo_image_too_small(
        self,
        client: TestClient,
        user_token: str,
        small_image_file
    ):
        """Test upload with image that's too small."""
        response = client.post(
            "/food-logs/from-photo",
            files={"photo": small_image_file},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 400
        assert "too small" in response.json()["detail"].lower()

    def test_upload_photo_rate_limit_exceeded(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db,
        valid_image_file
    ):
        """Test upload when rate limit is exceeded."""
        # Directly modify the test_user_in_db fixture since it's already in the correct session
        from datetime import date
        
        # Access the session through app overrides
        from app.db import get_session
        session_gen = client.app.dependency_overrides[get_session]()
        session = next(session_gen)
        
        # Get user from this session and modify
        user = session.get(User, 1)
        user.photo_count = 30
        user.last_photo_date = date.today()
        session.commit()
        
        # Try to upload
        response = client.post(
            "/food-logs/from-photo",
            files={"photo": valid_image_file},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 429
        assert "limit reached" in response.json()["detail"].lower()

    def test_upload_photo_no_food_detected(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db,
        valid_image_file
    ):
        """Test upload when no food is detected in image."""
        # Mock vision service to return empty list
        with patch('app.services.vision.VisionService.detect_food') as mock_detect:
            mock_detect.return_value = []
            
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 404
        assert "no food" in response.json()["detail"].lower()

    def test_upload_photo_nutrition_not_found(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db,
        valid_image_file
    ):
        """Test upload when nutrition data can't be found."""
        # Mock nutrition service to return None
        with patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = None
            
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 404
        assert "nutrition data" in response.json()["detail"].lower()

    def test_upload_photo_unauthorized(
        self,
        client: TestClient,
        valid_image_file
    ):
        """Test upload without authentication."""
        response = client.post(
            "/food-logs/from-photo",
            files={"photo": valid_image_file}
        )
        
        assert response.status_code == 401

    def test_upload_photo_multiple_predictions(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db,
        valid_image_file,
        mock_nutrition_data
    ):
        """Test upload with multiple food items detected."""
        # Mock vision service to return multiple items
        with patch('app.services.vision.VisionService.detect_food') as mock_vision:
            mock_vision.return_value = [
                {"label": "pizza", "confidence": 0.85, "source": "mock"},
                {"label": "salad", "confidence": 0.78, "source": "mock"},
                {"label": "drink", "confidence": 0.65, "source": "mock"}
            ]
            
            with patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_nutrition:
                mock_nutrition.return_value = mock_nutrition_data
                
                response = client.post(
                    "/food-logs/from-photo",
                    files={"photo": valid_image_file},
                    headers={"Authorization": f"Bearer {user_token}"}
                )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have predictions for all detected items
        assert len(data["predictions"]) >= 1

    def test_upload_photo_vision_api_error(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db,
        valid_image_file
    ):
        """Test upload when Vision API fails."""
        with patch('app.services.vision.VisionService.detect_food') as mock_detect:
            mock_detect.side_effect = Exception("Vision API error")
            
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 503
        assert "service" in response.json()["detail"].lower() or "unavailable" in response.json()["detail"].lower()

    def test_upload_photo_increments_rate_limit(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db,
        valid_image_file,
        mock_nutrition_data
    ):
        """Test that successful upload increments rate limit counter."""
        # Get user from the client's session
        from app.db import get_session
        session_gen = client.app.dependency_overrides[get_session]()
        session = next(session_gen)
        
        user = session.get(User, 1)
        initial_count = user.photo_count if user.photo_count else 0
        
        # Mock nutrition service
        with patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_nutrition_data
            
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 200
        
        # Verify count was incremented - refresh from session
        session_gen2 = client.app.dependency_overrides[get_session]()
        session2 = next(session_gen2)
        user_after = session2.get(User, 1)
        assert user_after.photo_count == initial_count + 1

    def test_upload_photo_returns_image_info(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db,
        valid_image_file,
        mock_nutrition_data
    ):
        """Test that response includes image validation info."""
        with patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_nutrition_data
            
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check image info
        assert "image_info" in data
        assert "format" in data["image_info"]
        assert "size_kb" in data["image_info"]
        assert data["image_info"]["format"] in ["jpeg", "jpg", "png", "webp"]

    def test_upload_photo_missing_file(
        self,
        client: TestClient,
        user_token: str
    ):
        """Test upload without providing a file."""
        response = client.post(
            "/food-logs/from-photo",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_upload_photo_handles_partial_nutrition_failures(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db,
        valid_image_file,
        mock_nutrition_data
    ):
        """Test that upload succeeds even if some nutrition lookups fail."""
        with patch('app.services.vision.VisionService.detect_food') as mock_vision:
            mock_vision.return_value = [
                {"label": "pizza", "confidence": 0.85, "source": "mock"},
                {"label": "unknown_food", "confidence": 0.75, "source": "mock"}
            ]
            
            with patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_nutrition:
                # First call succeeds, second fails
                mock_nutrition.side_effect = [mock_nutrition_data, Exception("Failed")]
                
                response = client.post(
                    "/food-logs/from-photo",
                    files={"photo": valid_image_file},
                    headers={"Authorization": f"Bearer {user_token}"}
                )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least one prediction (the successful one)
        assert len(data["predictions"]) >= 1
        assert data["predictions"][0]["label"] == "pizza"
