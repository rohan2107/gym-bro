"""Tests for photo meal logging endpoint."""

from typing import Any, Generator, cast

import pytest
from io import BytesIO
from PIL import Image
from unittest.mock import patch, AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import User


@pytest.fixture
def valid_image_file() -> tuple[str, BytesIO, str]:
    """Create a valid test image file."""
    image = Image.new('RGB', (500, 500), color='red')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return ("test_meal.jpg", buffer, "image/jpeg")


@pytest.fixture
def small_image_file() -> tuple[str, BytesIO, str]:
    """Create an image that's too small."""
    image = Image.new('RGB', (100, 100), color='blue')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return ("small.jpg", buffer, "image/jpeg")


@pytest.fixture
def mock_vision_predictions() -> list[dict[str, Any]]:
    """Mock Vision API predictions."""
    return [
        {
            "label": "pizza",
            "confidence": 0.85,
            "source": "mock_development"
        }
    ]


@pytest.fixture
def mock_nutrition_data() -> dict[str, Any]:
    """Mock USDA nutrition data."""
    return {
        "name": "Pizza, cheese, regular crust",
        "fdc_id": 174987,
        "calories": 265,
        "protein_g": 11.0,
        "carbs_g": 33.0,
        "fat_g": 10.0,
        "serving_size": "100g",
        "portion_g": 100.0,
        "confidence": "high"
    }


def _get_session_gen(client: TestClient) -> Generator[Session, None, None]:
    """Get a typed session generator from client's dependency overrides."""
    from app.db import get_session
    _app = cast(FastAPI, client.app)
    return cast(Generator[Session, None, None], _app.dependency_overrides[get_session]())


class TestPhotoMealLogging:
    """Test suite for photo meal logging endpoint."""

    def test_upload_photo_success(
        self, 
        client: TestClient, 
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
        mock_vision_predictions: list[dict[str, Any]],
        mock_nutrition_data: dict[str, Any]
    ) -> None:
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
    ) -> None:
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
        small_image_file: tuple[str, BytesIO, str]
    ) -> None:
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
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """Test upload when rate limit is exceeded."""
        # Directly modify the test_user_in_db fixture since it's already in the correct session
        from datetime import date
        
        # Access the session through app overrides
        session_gen = _get_session_gen(client)
        try:
            session = next(session_gen)
            
            # Get user from this session and modify
            user = session.get(User, 1)
            assert user is not None
            user.photo_count = 30
            user.last_photo_date = date.today()
            session.commit()
        finally:
            session_gen.close()
        
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
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """Test upload when no food is detected in image."""
        # Mock vision service to return empty list
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect:
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
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
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
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
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
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
        mock_nutrition_data: dict[str, Any]
    ) -> None:
        """Test upload with multiple food items detected."""
        # Mock vision service to return multiple items
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_vision:
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
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """Test upload when Vision API fails."""
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect:
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
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
        mock_nutrition_data: dict[str, Any]
    ) -> None:
        """Test that successful upload increments rate limit counter."""
        # Get user from the client's session
        session_gen = _get_session_gen(client)
        try:
            session = next(session_gen)
            
            user = session.get(User, 1)
            assert user is not None
            initial_count = user.photo_count if user.photo_count else 0
        finally:
            session_gen.close()
        
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
        session_gen2 = _get_session_gen(client)
        try:
            session2 = next(session_gen2)
            user_after = session2.get(User, 1)
            assert user_after is not None
            assert user_after.photo_count == initial_count + 1
        finally:
            session_gen2.close()

    def test_upload_photo_returns_image_info(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
        mock_nutrition_data: dict[str, Any]
    ) -> None:
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
    ) -> None:
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
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
        mock_nutrition_data: dict[str, Any]
    ) -> None:
        """Test that upload succeeds even if some nutrition lookups fail."""
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_vision:
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

    def test_upload_photo_refunds_quota_on_vision_error(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """Test that quota is refunded when Vision API fails."""
        # Check initial count
        from app.models import User
        session_gen = _get_session_gen(client)
        try:
            session = next(session_gen)
            user = session.get(User, 1)
            assert user is not None
            initial_count = user.photo_count
        finally:
            session_gen.close()
        
        # Mock vision service to raise error
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect:
            mock_detect.side_effect = Exception("Vision API error")
            
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 503
        
        # Verify count was refunded (should be same as initial)
        session_gen = _get_session_gen(client)
        try:
            session = next(session_gen)
            user = session.get(User, 1)
            assert user is not None
            assert user.photo_count == initial_count
        finally:
            session_gen.close()

    def test_provider_failure_returns_503_and_refunds_quota(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """A provider error (quota, block, bad response) fails closed and costs the user nothing."""
        from app.services.food_recognition import FoodRecognitionError

        session_gen = _get_session_gen(client)
        try:
            user = next(session_gen).get(User, 1)
            assert user is not None
            initial_count = user.photo_count
        finally:
            session_gen.close()

        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect:
            mock_detect.side_effect = FoodRecognitionError("Gemini request failed")

            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )

        assert response.status_code == 503
        # The provider's own message is for logs, not clients.
        assert "Gemini" not in response.json()["detail"]

        session_gen = _get_session_gen(client)
        try:
            user = next(session_gen).get(User, 1)
            assert user is not None
            assert user.photo_count == initial_count
        finally:
            session_gen.close()

    def test_nutrition_lookup_failure_is_a_503_not_a_misleading_404_and_refunds_quota(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """USDA erroring is "try again", not "we found no nutrition data"."""
        from app.services.nutrition import NutritionLookupError

        session_gen = _get_session_gen(client)
        try:
            user = next(session_gen).get(User, 1)
            assert user is not None
            initial_count = user.photo_count
        finally:
            session_gen.close()

        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect, \
             patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_search:
            mock_detect.return_value = [{"label": "banana", "confidence": 0.9, "source": "gemini"}]
            mock_search.side_effect = NutritionLookupError("USDA returned 403")

            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )

        assert response.status_code == 503
        assert "USDA" not in response.json()["detail"]
        assert "manually" in response.json()["detail"]

        session_gen = _get_session_gen(client)
        try:
            user = next(session_gen).get(User, 1)
            assert user is not None
            assert user.photo_count == initial_count
        finally:
            session_gen.close()

    def test_no_nutrition_match_is_still_a_404(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect, \
             patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_search:
            mock_detect.return_value = [{"label": "unobtainium", "confidence": 0.9, "source": "gemini"}]
            mock_search.return_value = None

            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )

        assert response.status_code == 404

    def test_one_failed_lookup_does_not_hide_the_foods_that_were_found(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
        mock_nutrition_data: dict[str, Any]
    ) -> None:
        from app.services.nutrition import NutritionLookupError

        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect, \
             patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_search:
            mock_detect.return_value = [
                {"label": "banana", "confidence": 0.9, "source": "gemini"},
                {"label": "pizza", "confidence": 0.8, "source": "gemini"},
            ]
            mock_search.side_effect = [NutritionLookupError("USDA returned 503"), mock_nutrition_data]

            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )

        assert response.status_code == 200
        assert [p["label"] for p in response.json()["predictions"]] == ["pizza"]

    def _post_photo(self, client, user_token, valid_image_file, predictions, search_result=None, search_side_effect=None):
        """Run the endpoint with the recognizer and USDA replaced."""
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect, \
             patch('app.services.nutrition.NutritionService.search_food', new_callable=AsyncMock) as mock_search:
            mock_detect.return_value = predictions
            mock_search.return_value = search_result
            if search_side_effect is not None:
                mock_search.side_effect = search_side_effect
            return client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )

    PIZZA_WITH_ESTIMATE = {
        "label": "pizza", "confidence": 0.9, "source": "gemini", "portion_g": 300,
        "estimate": {"calories": 800, "protein_g": 30.0, "carbs_g": 90.0, "fat_g": 32.0},
    }

    def test_usda_values_are_scaled_to_the_estimated_portion(
        self, client: TestClient, user_token: str, test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str], mock_nutrition_data: dict[str, Any]
    ) -> None:
        response = self._post_photo(
            client, user_token, valid_image_file, [self.PIZZA_WITH_ESTIMATE], mock_nutrition_data
        )

        assert response.status_code == 200
        nutrition = response.json()["predictions"][0]["nutrition"]
        assert nutrition["source"] == "usda"
        assert nutrition["serving_size"] == "300g"
        assert nutrition["calories"] == round(mock_nutrition_data["calories"] * 3)

    def test_usda_values_stay_per_100g_when_no_portion_was_estimated(
        self, client: TestClient, user_token: str, test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str], mock_nutrition_data: dict[str, Any]
    ) -> None:
        bare = {"label": "pizza", "confidence": 0.9, "source": "gemini", "portion_g": None, "estimate": None}

        response = self._post_photo(client, user_token, valid_image_file, [bare], mock_nutrition_data)

        nutrition = response.json()["predictions"][0]["nutrition"]
        assert nutrition["source"] == "usda"
        assert nutrition["serving_size"] == "100g"
        assert nutrition["calories"] == mock_nutrition_data["calories"]

    def test_a_usda_failure_falls_back_to_the_models_own_estimate(
        self, client: TestClient, user_token: str, test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """USDA erroring degrades accuracy, not availability."""
        from app.services.nutrition import NutritionLookupError

        response = self._post_photo(
            client, user_token, valid_image_file, [self.PIZZA_WITH_ESTIMATE],
            search_side_effect=NutritionLookupError("USDA returned 503"),
        )

        assert response.status_code == 200
        nutrition = response.json()["predictions"][0]["nutrition"]
        assert nutrition["source"] == "ai_estimate"
        assert nutrition["calories"] == 800
        assert nutrition["serving_size"] == "300g"
        assert nutrition["fdc_id"] is None

    def test_no_usda_match_also_falls_back_to_the_estimate(
        self, client: TestClient, user_token: str, test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        response = self._post_photo(
            client, user_token, valid_image_file, [self.PIZZA_WITH_ESTIMATE], search_result=None
        )

        assert response.status_code == 200
        assert response.json()["predictions"][0]["nutrition"]["source"] == "ai_estimate"

    def test_a_slow_usda_lookup_is_cut_off_and_falls_back(
        self, client: TestClient, user_token: str, test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str], monkeypatch
    ) -> None:
        import asyncio

        from app.routers import food_logs

        async def slow_search(self, query):
            await asyncio.sleep(5)

        monkeypatch.setattr(food_logs, "NUTRITION_LOOKUP_BUDGET_SECONDS", 0.05)
        with patch('app.services.nutrition.NutritionService.search_food', slow_search), \
             patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = [self.PIZZA_WITH_ESTIMATE]
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )

        assert response.status_code == 200
        assert response.json()["predictions"][0]["nutrition"]["source"] == "ai_estimate"

    def test_an_estimate_without_a_portion_is_not_used(
        self, client: TestClient, user_token: str, test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """Macros with no stated portion cannot be labelled honestly, so USDA failing is a 503."""
        from app.services.nutrition import NutritionLookupError

        odd = {**self.PIZZA_WITH_ESTIMATE, "portion_g": None}

        response = self._post_photo(
            client, user_token, valid_image_file, [odd],
            search_side_effect=NutritionLookupError("USDA returned 503"),
        )

        assert response.status_code == 503

    def test_the_other_foods_still_use_usda_when_only_one_lookup_fails(
        self, client: TestClient, user_token: str, test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str], mock_nutrition_data: dict[str, Any]
    ) -> None:
        from app.services.nutrition import NutritionLookupError

        rice = {"label": "rice", "confidence": 0.8, "source": "gemini", "portion_g": 150,
                "estimate": {"calories": 200, "protein_g": 4.0, "carbs_g": 44.0, "fat_g": 0.5}}

        response = self._post_photo(
            client, user_token, valid_image_file, [self.PIZZA_WITH_ESTIMATE, rice],
            search_side_effect=[NutritionLookupError("USDA returned 503"), mock_nutrition_data],
        )

        sources = {p["label"]: p["nutrition"]["source"] for p in response.json()["predictions"]}
        assert sources == {"pizza": "ai_estimate", "rice": "usda"}

    def test_the_image_mime_type_reaches_the_provider(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = []

            client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )

        assert mock_detect.call_args.kwargs["mime_type"] == "image/jpeg"

    def test_upload_photo_refunds_quota_on_no_food_detected(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """Test that quota is refunded when no food is detected."""
        # Check initial count
        from app.models import User
        session_gen = _get_session_gen(client)
        try:
            session = next(session_gen)
            user = session.get(User, 1)
            assert user is not None
            initial_count = user.photo_count
        finally:
            session_gen.close()
        
        # Mock vision service to return empty list
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = []
            
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 404
        
        # Verify count was refunded
        session_gen = _get_session_gen(client)
        try:
            session = next(session_gen)
            user = session.get(User, 1)
            assert user is not None
            assert user.photo_count == initial_count
        finally:
            session_gen.close()

    def test_upload_photo_refunds_quota_on_no_nutrition_found(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str]
    ) -> None:
        """Test that quota is refunded when no nutrition data is found."""
        # Check initial count
        from app.models import User
        session_gen = _get_session_gen(client)
        try:
            session = next(session_gen)
            user = session.get(User, 1)
            assert user is not None
            initial_count = user.photo_count
        finally:
            session_gen.close()
        
        # Mock services
        with patch('app.services.gemini.GeminiRecognizer.detect_food', new_callable=AsyncMock) as mock_detect, \
             patch('app.services.nutrition.NutritionService.search_food') as mock_search:
            
            mock_detect.return_value = [{"label": "pizza", "confidence": 0.85, "source": "mock"}]
            mock_search.return_value = None  # No nutrition found
            
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        assert response.status_code == 404
        
        # Verify count was refunded
        session_gen = _get_session_gen(client)
        try:
            session = next(session_gen)
            user = session.get(User, 1)
            assert user is not None
            assert user.photo_count == initial_count
        finally:
            session_gen.close()


class TestMockModeOnDeployment:
    """Fabricated sample data must never be served from a real deployment."""

    def test_photo_analysis_refused_when_keys_missing_on_vercel(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
    ) -> None:
        with patch.dict("os.environ", {"VERCEL": "1"}):
            response = client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"},
            )

        assert response.status_code == 503
        assert "log this meal manually" in response.json()["detail"]

    def test_refusal_does_not_spend_quota(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
    ) -> None:
        with patch.dict("os.environ", {"VERCEL": "1"}):
            client.post(
                "/food-logs/from-photo",
                files={"photo": valid_image_file},
                headers={"Authorization": f"Bearer {user_token}"},
            )

        session = next(_get_session_gen(client))
        assert session.get(User, 1).photo_count == 0

    def test_mock_mode_still_works_locally(
        self,
        client: TestClient,
        user_token: str,
        test_user_in_db: User,
        valid_image_file: tuple[str, BytesIO, str],
    ) -> None:
        """Development keeps its mock behaviour."""
        response = client.post(
            "/food-logs/from-photo",
            files={"photo": valid_image_file},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
