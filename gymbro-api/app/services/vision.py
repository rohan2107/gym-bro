"""Google Cloud Vision integration for food detection.

Calls the Vision REST API (``images:annotate``) directly with an API key rather
than using the ``google-cloud-vision`` client library. Three reasons:

1. The client library authenticates with service-account credentials, not API
   keys — but an API key (``GOOGLE_VISION_API_KEY``) is what this app is
   configured and deployed with.
2. It pulls in gRPC and protobuf, which is a large dependency to ship into a
   Vercel serverless function for what is one HTTP POST.
3. ``httpx`` is already a dependency and already async, so this matches how
   ``NutritionService`` talks to USDA.
"""

import base64
import logging
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings


logger = logging.getLogger(__name__)

# Generic labels Vision returns for almost every food photo. They are true but
# useless as USDA search terms ("food" matches nothing meaningful), so they are
# dropped before nutrition lookup.
NON_FOOD_LABELS = frozenset(
    {
        "baked goods",
        "comfort food",
        "cuisine",
        "cutlery",
        "delicacy",
        "dish",
        "dishware",
        "drinkware",
        "fast food",
        "finger food",
        "food",
        "food group",
        "foodie",
        "fork",
        "garnish",
        "ingredient",
        "junk food",
        "kitchen utensil",
        "knife",
        "meal",
        "natural foods",
        "plate",
        "produce",
        "recipe",
        "serveware",
        "side dish",
        "spoon",
        "staple food",
        "styles",
        "super food",
        "table",
        "tableware",
        "vegan nutrition",
        "vegetarian food",
        "whole food",
    }
)


class VisionService:
    """Detects food items in images using the Google Cloud Vision API."""

    BASE_URL = "https://vision.googleapis.com/v1"
    TIMEOUT_SECONDS = 10.0

    # Vision label scores are probabilities in [0, 1].
    LABEL_CONFIDENCE_THRESHOLD = 0.70
    # Web-entity scores are unbounded relevance scores, not probabilities, and
    # routinely exceed 1.0. They are thresholded on the raw value and clamped
    # before being reported as a confidence.
    WEB_ENTITY_SCORE_THRESHOLD = 0.60
    MAX_PREDICTIONS = 3

    def __init__(self, mock_mode: Optional[bool] = None):
        """Initialize the Vision API client.

        Args:
            mock_mode: Force mock mode (True) or real API calls (False). When
                None, mock mode is enabled if no API key is configured.
        """
        self.api_key = settings.GOOGLE_VISION_API_KEY or None

        if mock_mode is None:
            mock_mode = not self.api_key

        self.mock_mode = mock_mode

    async def detect_food(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> List[Dict[str, Any]]:
        """Detect food items in an image, most confident first.

        Args:
            image_bytes: Raw image data.
            mime_type: Accepted for interface parity; Vision detects the type itself.

        Returns:
            Up to ``MAX_PREDICTIONS`` predictions, e.g.::

                [{"label": "pizza", "confidence": 0.92, "source": "vision_label"}]

            An empty list means nothing recognisable as a specific food was
            found; the caller decides how to handle that.

        Raises:
            RuntimeError: If real mode is requested without an API key.
            httpx.HTTPError: If the Vision API call fails.
        """
        if self.mock_mode:
            return [
                {
                    "label": "pizza",
                    "confidence": 0.85,
                    "source": "mock_development",
                }
            ]

        if not self.api_key:
            raise RuntimeError(
                "Vision API key not configured but mock mode is disabled. "
                "Set GOOGLE_VISION_API_KEY or enable mock mode."
            )

        payload = {
            "requests": [
                {
                    "image": {"content": base64.b64encode(image_bytes).decode("ascii")},
                    "features": [
                        {"type": "LABEL_DETECTION", "maxResults": 20},
                        {"type": "WEB_DETECTION", "maxResults": 20},
                    ],
                }
            ]
        }

        # The key goes in a header, not a query parameter. httpx puts the full
        # request URL into HTTPStatusError's message, and this endpoint's caller
        # logs that exception with exc_info=True - a `?key=` would put the
        # credential straight into application logs.
        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.BASE_URL}/images:annotate",
                headers={"X-Goog-Api-Key": self.api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return self._extract_predictions(data)

    def _extract_predictions(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Turn a Vision annotate response into ranked, deduplicated predictions.

        Vision reports per-image failures inside a 200 response, so the error
        field is checked here rather than relying on the HTTP status.
        """
        responses = data.get("responses") or []
        if not responses:
            return []

        annotation = responses[0]

        error = annotation.get("error")
        if error:
            message = error.get("message", "unknown error")
            raise httpx.HTTPError(f"Vision API returned an error: {message}")

        candidates: List[Dict[str, Any]] = []

        for label in annotation.get("labelAnnotations") or []:
            score = label.get("score") or 0.0
            description = (label.get("description") or "").strip().lower()
            if not description or score < self.LABEL_CONFIDENCE_THRESHOLD:
                continue
            candidates.append(
                {
                    "label": description,
                    "confidence": round(min(float(score), 1.0), 4),
                    "source": "vision_label",
                }
            )

        web_entities = (annotation.get("webDetection") or {}).get("webEntities") or []
        for entity in web_entities:
            score = entity.get("score") or 0.0
            description = (entity.get("description") or "").strip().lower()
            if not description or score < self.WEB_ENTITY_SCORE_THRESHOLD:
                continue
            candidates.append(
                {
                    "label": description,
                    # Clamped: web-entity scores are relevance, not probability.
                    "confidence": round(min(float(score), 1.0), 4),
                    "source": "web_entity",
                }
            )

        # Highest confidence wins for a given label; generic terms are dropped.
        best_by_label: Dict[str, Dict[str, Any]] = {}
        for candidate in sorted(
            candidates, key=lambda c: c["confidence"], reverse=True
        ):
            label = candidate["label"]
            if label in NON_FOOD_LABELS or label in best_by_label:
                continue
            best_by_label[label] = candidate

        return list(best_by_label.values())[: self.MAX_PREDICTIONS]
