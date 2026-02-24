"""Google Cloud Vision API integration for food detection.

This service uses Google Cloud Vision API to detect food items in images
with confidence scores.
"""

import os
from typing import Any, Dict, List, Optional

# Note: uncomment when API key is configured
# from google.cloud import vision
# from google.cloud.vision_v1 import types


class VisionService:
    """Service for detecting food items in images using Google Cloud Vision API."""

    def __init__(self, mock_mode: Optional[bool] = None):
        """Initialize the Vision API client.
        
        Args:
            mock_mode: Force mock mode (True) or prod mode (False).
                      If None, auto-detect based on API key presence.
        
        In mock mode, returns dummy predictions for testing.
        """
        self.api_key = os.getenv("GOOGLE_VISION_API_KEY")
        
        # Auto-detect mock mode if not explicitly set
        if mock_mode is None:
            mock_mode = not self.api_key
        
        self.mock_mode = mock_mode
        
        # Only raise error if mock_mode is explicitly False and no API key
        # (mock_mode=False in tests with HTTP mocking is allowed)
        if mock_mode is False and not self.api_key:
            # This is intentionally allowed for testing with HTTP mocks
            # The actual API calls will fail if attempted without a key
            pass
        
        # TODO: Initialize real Vision API client when API key is configured
        # Uncomment lines 10-11 (import statements) and replace this:
        self.client = None

    def detect_food(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Detect food items in image with confidence scores.
        
        Args:
            image_bytes: Raw image data as bytes
            
        Returns:
            List of predictions with format:
            [
                {
                    "label": "pizza",
                    "confidence": 0.92,
                    "source": "vision_label"
                },
                {
                    "label": "salad",
                    "confidence": 0.78,
                    "source": "web_entity"
                }
            ]
            
        Raises:
            Exception: If Vision API call fails
        """
        # Return mock data in development/test mode
        if self.mock_mode:
            return [
                {
                    "label": "pizza",
                    "confidence": 0.85,
                    "source": "mock_development"
                }
            ]
        
        # Production mode but client not initialized
        if self.client is None:
            raise RuntimeError(
                "Vision API client not initialized. Mock mode is disabled but client is None. "
                "This is a configuration error - either enable mock mode or initialize the real client."
            )
        
        # Real implementation (uncomment after API setup):
        # image = vision.Image(content=image_bytes)
        # 
        # # Use label detection + web detection for best results
        # labels_response = self.client.label_detection(image=image)
        # web_response = self.client.web_detection(image=image)
        # 
        # predictions = []
        # 
        # # Extract food-related labels with confidence > 70%
        # for label in labels_response.label_annotations:
        #     if label.score > 0.70:
        #         predictions.append({
        #             "label": label.description.lower(),
        #             "confidence": label.score,
        #             "source": "vision_label"
        #         })
        # 
        # # Add web entities (often more specific, lower threshold)
        # for entity in web_response.web_detection.web_entities:
        #     if entity.score > 0.60:
        #         predictions.append({
        #             "label": entity.description.lower(),
        #             "confidence": entity.score,
        #             "source": "web_entity"
        #         })
        # 
        # # Sort by confidence, deduplicate, return top 3
        # seen = set()
        # unique_predictions = []
        # for pred in sorted(predictions, key=lambda x: x["confidence"], reverse=True):
        #     if pred["label"] not in seen:
        #         seen.add(pred["label"])
        #         unique_predictions.append(pred)
        #         if len(unique_predictions) >= 3:
        #             break
        # 
        # return unique_predictions

    def validate_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Validate that image is suitable for food detection.
        
        Args:
            image_bytes: Raw image data
            
        Returns:
            Dict with validation results:
            {
                "valid": True/False,
                "error": "error message if invalid",
                "format": "jpeg/png/etc",
                "size_kb": 123
            }
        """
        import io
        from PIL import Image
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            size_kb = len(image_bytes) / 1024
            
            # Check file size (max 10MB)
            if size_kb > 10 * 1024:
                return {
                    "valid": False,
                    "error": "Image too large. Maximum size is 10MB.",
                }
            
            # Check format
            if image.format.lower() not in ["jpeg", "jpg", "png", "webp"]:
                return {
                    "valid": False,
                    "error": f"Unsupported format: {image.format}. Use JPEG, PNG, or WebP.",
                }
            
            # Check dimensions (reasonable size)
            if image.width < 200 or image.height < 200:
                return {
                    "valid": False,
                    "error": "Image too small. Minimum size is 200x200 pixels.",
                }
            
            return {
                "valid": True,
                "format": image.format.lower(),
                "size_kb": round(size_kb, 2),
                "dimensions": f"{image.width}x{image.height}"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid image file: {str(e)}"
            }
