"""The contract every food-recognition provider implements.

The photo endpoint depends on this interface, not on a particular provider, so the
provider is a configuration choice (``FOOD_RECOGNITION_PROVIDER``) and swapping it needs no
code change. See docs/adr/0005-food-recognition-providers.md.
"""

from typing import Any, Dict, List, Protocol


# One recognised food: {"label": str, "confidence": float in [0, 1], "source": str}.
Prediction = Dict[str, Any]


class FoodRecognitionError(Exception):
    """A provider could not produce a usable answer.

    Raised for anything that is the provider's fault rather than the user's: a network
    failure, a quota or rate limit, a blocked or malformed response. The endpoint turns it
    into a 503 and refunds the user's quota. The message is for logs, never for clients.
    """


class FoodRecognizer(Protocol):
    """Finds the foods in a meal photo."""

    # True when no credentials are configured and the provider returns fixed sample data.
    # Acceptable for local development; the endpoint refuses to serve it on a deployment.
    mock_mode: bool

    async def detect_food(
        self, image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> List[Prediction]:
        """Return up to a few predictions, most confident first.

        An empty list means no food was recognised. Provider failures raise
        ``FoodRecognitionError`` (or any other exception, which the endpoint also treats as
        a provider failure).
        """
        ...
