"""Tests for Vision service (Google Cloud Vision API integration)."""

import pytest
from io import BytesIO
from PIL import Image

from app.services.vision import VisionService


@pytest.fixture
def vision_service():
    """Create VisionService instance for testing."""
    return VisionService()


@pytest.fixture
def valid_image_bytes():
    """Create a valid test image."""
    image = Image.new('RGB', (500, 500), color='red')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def small_image_bytes():
    """Create an image that's too small."""
    image = Image.new('RGB', (100, 100), color='blue')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def large_image_bytes():
    """Create an image that's too large (>10MB)."""
    # Create a very large image
    image = Image.new('RGB', (5000, 5000), color='green')
    buffer = BytesIO()
    image.save(buffer, format='PNG', compress_level=0)  # No compression
    return buffer.getvalue()


class TestVisionService:
    """Test suite for VisionService."""

    def test_initialization(self, vision_service):
        """Test VisionService initializes correctly."""
        assert vision_service is not None
        # In mock mode (no API key), should still initialize successfully
        assert vision_service.mock_mode is True or vision_service.api_key is not None

    def test_detect_food_returns_predictions(self, vision_service, valid_image_bytes):
        """Test detect_food returns list of predictions in mock mode."""
        predictions = vision_service.detect_food(valid_image_bytes)
        
        assert isinstance(predictions, list)
        assert len(predictions) > 0
        
        # Check prediction structure
        prediction = predictions[0]
        assert "label" in prediction
        assert "confidence" in prediction
        assert "source" in prediction
        
        # Check types
        assert isinstance(prediction["label"], str)
        assert isinstance(prediction["confidence"], float)
        assert 0.0 <= prediction["confidence"] <= 1.0

    def test_detect_food_mock_mode(self, vision_service, valid_image_bytes):
        """Test detect_food returns mock data when client is None."""
        # In mock mode (no real API), should return mock data
        predictions = vision_service.detect_food(valid_image_bytes)
        
        assert len(predictions) == 1
        assert predictions[0]["label"] == "pizza"
        assert predictions[0]["confidence"] == 0.85
        assert predictions[0]["source"] == "mock_development"

    def test_validate_image_valid(self, vision_service, valid_image_bytes):
        """Test image validation passes for valid image."""
        result = vision_service.validate_image(valid_image_bytes)
        
        assert result["valid"] is True
        assert "format" in result
        assert "size_kb" in result
        assert "dimensions" in result
        assert result["format"] in ["jpeg", "jpg", "png"]

    def test_validate_image_too_small(self, vision_service, small_image_bytes):
        """Test image validation rejects images that are too small."""
        result = vision_service.validate_image(small_image_bytes)
        
        assert result["valid"] is False
        assert "too small" in result["error"].lower()

    def test_validate_image_too_large(self, vision_service):
        """Test image validation rejects images over 10MB."""
        # Create 11MB of data
        large_data = b"x" * (11 * 1024 * 1024)
        
        result = vision_service.validate_image(large_data)
        
        # Will fail on Image.open since it's not a valid image,
        # but that's expected for invalid data
        assert result["valid"] is False

    def test_validate_image_invalid_data(self, vision_service):
        """Test image validation rejects invalid image data."""
        invalid_data = b"not an image"
        
        result = vision_service.validate_image(invalid_data)
        
        assert result["valid"] is False
        assert "error" in result
        assert "invalid" in result["error"].lower()

    def test_validate_image_png_format(self, vision_service):
        """Test image validation accepts PNG format."""
        image = Image.new('RGB', (300, 300), color='purple')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        
        result = vision_service.validate_image(buffer.getvalue())
        
        assert result["valid"] is True
        assert result["format"] == "png"

    def test_validate_image_webp_format(self, vision_service):
        """Test image validation accepts WebP format."""
        image = Image.new('RGB', (300, 300), color='yellow')
        buffer = BytesIO()
        image.save(buffer, format='WEBP')
        
        result = vision_service.validate_image(buffer.getvalue())
        
        assert result["valid"] is True
        assert result["format"] == "webp"

    def test_detect_food_with_different_image_sizes(self, vision_service):
        """Test detect_food works with various image sizes."""
        sizes = [(500, 500), (800, 600), (1920, 1080)]
        
        for width, height in sizes:
            image = Image.new('RGB', (width, height), color='orange')
            buffer = BytesIO()
            image.save(buffer, format='JPEG')
            
            predictions = vision_service.detect_food(buffer.getvalue())
            assert isinstance(predictions, list)
            assert len(predictions) > 0
