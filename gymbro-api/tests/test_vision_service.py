"""Tests for Vision service (Google Cloud Vision API integration)."""

import httpx
import pytest
import respx
from io import BytesIO
from PIL import Image

from app.services.vision import VisionService


ANNOTATE_URL = f"{VisionService.BASE_URL}/images:annotate"


@pytest.fixture
def vision_service():
    """VisionService in mock mode (no API key, no network)."""
    return VisionService(mock_mode=True)


@pytest.fixture
def real_vision_service(monkeypatch):
    """VisionService configured to make (mocked) real API calls."""
    from app.config import settings

    monkeypatch.setattr(settings, "GOOGLE_VISION_API_KEY", "test-api-key")
    return VisionService(mock_mode=False)


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


def annotate_response(
    labels: list[tuple[str, float]] | None = None,
    web_entities: list[tuple[str, float]] | None = None,
    error: dict | None = None,
) -> dict:
    """Build a Vision images:annotate response body."""
    annotation: dict = {}
    if error is not None:
        annotation["error"] = error
    if labels is not None:
        annotation["labelAnnotations"] = [
            {"description": description, "score": score} for description, score in labels
        ]
    if web_entities is not None:
        annotation["webDetection"] = {
            "webEntities": [
                {"description": description, "score": score}
                for description, score in web_entities
            ]
        }
    return {"responses": [annotation]}


class TestVisionServiceMockMode:
    """Behaviour when no API key is configured."""

    def test_initialization(self, vision_service):
        """Test VisionService initializes correctly."""
        assert vision_service is not None
        assert vision_service.mock_mode is True

    def test_auto_detects_mock_mode_without_key(self):
        """Without an API key, mock mode turns itself on."""
        assert VisionService().mock_mode is True

    def test_auto_detects_real_mode_with_key(self, monkeypatch):
        """With an API key, mock mode stays off."""
        from app.config import settings

        monkeypatch.setattr(settings, "GOOGLE_VISION_API_KEY", "test-api-key")
        service = VisionService()
        assert service.mock_mode is False
        assert service.api_key == "test-api-key"

    async def test_detect_food_returns_predictions(self, vision_service, valid_image_bytes):
        """Test detect_food returns list of predictions in mock mode."""
        predictions = await vision_service.detect_food(valid_image_bytes)

        assert isinstance(predictions, list)
        assert len(predictions) > 0

        prediction = predictions[0]
        assert "label" in prediction
        assert "confidence" in prediction
        assert "source" in prediction

        assert isinstance(prediction["label"], str)
        assert isinstance(prediction["confidence"], float)
        assert 0.0 <= prediction["confidence"] <= 1.0

    async def test_detect_food_mock_mode(self, vision_service, valid_image_bytes):
        """Test detect_food returns mock data in mock mode."""
        predictions = await vision_service.detect_food(valid_image_bytes)

        assert len(predictions) == 1
        assert predictions[0]["label"] == "pizza"
        assert predictions[0]["confidence"] == 0.85
        assert predictions[0]["source"] == "mock_development"

    async def test_detect_food_makes_no_network_calls(self, vision_service, valid_image_bytes):
        """Mock mode must not touch the network."""
        with respx.mock(assert_all_called=False) as mock:
            route = mock.post(ANNOTATE_URL)
            await vision_service.detect_food(valid_image_bytes)
            assert not route.called

    async def test_detect_food_with_different_image_sizes(self, vision_service):
        """Test detect_food works with various image sizes."""
        sizes = [(500, 500), (800, 600), (1920, 1080)]

        for width, height in sizes:
            image = Image.new('RGB', (width, height), color='orange')
            buffer = BytesIO()
            image.save(buffer, format='JPEG')

            predictions = await vision_service.detect_food(buffer.getvalue())
            assert isinstance(predictions, list)
            assert len(predictions) > 0


class TestVisionServiceRealMode:
    """Behaviour against the Vision REST API."""

    async def test_raises_without_api_key(self, valid_image_bytes):
        """Real mode without a key is a configuration error, not a silent mock."""
        service = VisionService(mock_mode=False)
        assert service.api_key is None

        with pytest.raises(RuntimeError, match="not configured"):
            await service.detect_food(valid_image_bytes)

    @respx.mock
    async def test_sends_base64_image_and_api_key(self, real_vision_service, valid_image_bytes):
        """The request carries the key as a query param and the image as base64."""
        import base64

        route = respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(200, json=annotate_response(labels=[("pizza", 0.95)]))
        )

        await real_vision_service.detect_food(valid_image_bytes)

        assert route.called
        request = route.calls.last.request
        assert request.url.params["key"] == "test-api-key"

        import json

        body = json.loads(request.content)
        image_content = body["requests"][0]["image"]["content"]
        assert base64.b64decode(image_content) == valid_image_bytes

        requested_features = {f["type"] for f in body["requests"][0]["features"]}
        assert requested_features == {"LABEL_DETECTION", "WEB_DETECTION"}

    @respx.mock
    async def test_parses_labels_and_web_entities(self, real_vision_service, valid_image_bytes):
        """Both annotation sources are returned, tagged by source."""
        respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(
                200,
                json=annotate_response(
                    labels=[("pizza", 0.95)],
                    web_entities=[("margherita pizza", 0.88)],
                ),
            )
        )

        predictions = await real_vision_service.detect_food(valid_image_bytes)

        by_label = {p["label"]: p for p in predictions}
        assert by_label["pizza"]["source"] == "vision_label"
        assert by_label["margherita pizza"]["source"] == "web_entity"

    @respx.mock
    async def test_filters_low_confidence_labels(self, real_vision_service, valid_image_bytes):
        """Labels below the confidence threshold are dropped."""
        respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(
                200,
                json=annotate_response(labels=[("pizza", 0.95), ("lasagna", 0.40)]),
            )
        )

        predictions = await real_vision_service.detect_food(valid_image_bytes)

        assert [p["label"] for p in predictions] == ["pizza"]

    @respx.mock
    async def test_filters_generic_non_food_labels(self, real_vision_service, valid_image_bytes):
        """Generic terms are useless as USDA queries and must be dropped."""
        respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(
                200,
                json=annotate_response(
                    labels=[
                        ("food", 0.99),
                        ("tableware", 0.98),
                        ("ingredient", 0.97),
                        ("dish", 0.96),
                        ("pizza", 0.92),
                    ]
                ),
            )
        )

        predictions = await real_vision_service.detect_food(valid_image_bytes)

        assert [p["label"] for p in predictions] == ["pizza"]

    @respx.mock
    async def test_clamps_web_entity_scores_above_one(self, real_vision_service, valid_image_bytes):
        """Web-entity scores are relevance values and can exceed 1.0."""
        respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(
                200,
                json=annotate_response(web_entities=[("pad thai", 2.47)]),
            )
        )

        predictions = await real_vision_service.detect_food(valid_image_bytes)

        assert predictions[0]["label"] == "pad thai"
        assert predictions[0]["confidence"] == 1.0

    @respx.mock
    async def test_deduplicates_keeping_highest_confidence(
        self, real_vision_service, valid_image_bytes
    ):
        """A label found by both sources appears once, at its best score."""
        respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(
                200,
                json=annotate_response(
                    labels=[("pizza", 0.75)],
                    web_entities=[("pizza", 0.95)],
                ),
            )
        )

        predictions = await real_vision_service.detect_food(valid_image_bytes)

        assert len(predictions) == 1
        assert predictions[0]["confidence"] == 0.95

    @respx.mock
    async def test_returns_predictions_sorted_and_capped(
        self, real_vision_service, valid_image_bytes
    ):
        """Results are ordered by confidence and capped at MAX_PREDICTIONS."""
        respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(
                200,
                json=annotate_response(
                    labels=[
                        ("pizza", 0.80),
                        ("lasagna", 0.95),
                        ("garlic bread", 0.90),
                        ("salad", 0.85),
                    ]
                ),
            )
        )

        predictions = await real_vision_service.detect_food(valid_image_bytes)

        assert len(predictions) == VisionService.MAX_PREDICTIONS
        confidences = [p["confidence"] for p in predictions]
        assert confidences == sorted(confidences, reverse=True)
        assert [p["label"] for p in predictions] == ["lasagna", "garlic bread", "salad"]

    @respx.mock
    async def test_returns_empty_when_nothing_detected(
        self, real_vision_service, valid_image_bytes
    ):
        """A photo with no recognisable food yields no predictions, not an error."""
        respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(200, json=annotate_response(labels=[]))
        )

        assert await real_vision_service.detect_food(valid_image_bytes) == []

    @respx.mock
    async def test_raises_on_per_image_error(self, real_vision_service, valid_image_bytes):
        """Vision reports image-level failures inside a 200 response."""
        respx.post(ANNOTATE_URL).mock(
            return_value=httpx.Response(
                200,
                json=annotate_response(error={"code": 3, "message": "Bad image data"}),
            )
        )

        with pytest.raises(httpx.HTTPError, match="Bad image data"):
            await real_vision_service.detect_food(valid_image_bytes)

    @respx.mock
    async def test_raises_on_http_error(self, real_vision_service, valid_image_bytes):
        """An HTTP failure propagates so the endpoint can refund quota."""
        respx.post(ANNOTATE_URL).mock(return_value=httpx.Response(403, json={}))

        with pytest.raises(httpx.HTTPStatusError):
            await real_vision_service.detect_food(valid_image_bytes)

    @respx.mock
    async def test_raises_on_timeout(self, real_vision_service, valid_image_bytes):
        """Timeouts propagate rather than returning empty predictions."""
        respx.post(ANNOTATE_URL).mock(side_effect=httpx.ConnectTimeout("timed out"))

        with pytest.raises(httpx.ConnectTimeout):
            await real_vision_service.detect_food(valid_image_bytes)

    @respx.mock
    async def test_handles_empty_responses_array(self, real_vision_service, valid_image_bytes):
        """A malformed response body degrades to no predictions."""
        respx.post(ANNOTATE_URL).mock(return_value=httpx.Response(200, json={"responses": []}))

        assert await real_vision_service.detect_food(valid_image_bytes) == []


class TestValidateImage:
    """Image validation runs locally, before any API call."""

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
