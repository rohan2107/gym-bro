"""Tests for the Gemini food-recognition provider.

Responses in tests/fixtures/gemini/ were recorded from the live API (model
gemini-3.5-flash-lite, 2026-09-21) with the same request this module sends, so the parser is
tested against the real response shape. Nothing here makes a live call.
"""

import json
from pathlib import Path

import httpx
import pytest
import respx

from app.config import settings
from app.services.food_recognition import FoodRecognitionError
from app.services.gemini import GeminiRecognizer

FIXTURES = Path(__file__).parent / "fixtures" / "gemini"
PRIMARY = "gemini-3.5-flash-lite"
FALLBACK = "gemini-3.1-flash-lite"
KEY = "test-gemini-key-do-not-leak"
IMAGE = b"\xff\xd8\xff\xe0 not a real jpeg, the API is mocked"


def url(model: str) -> str:
    return f"{GeminiRecognizer.BASE_URL}/{model}:generateContent"


def recorded(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def answer(*foods: dict) -> dict:
    """A minimal successful response carrying the given foods."""
    return {
        "candidates": [
            {"content": {"parts": [{"text": json.dumps({"foods": list(foods)})}]}}
        ]
    }


@pytest.fixture
def recognizer(monkeypatch) -> GeminiRecognizer:
    monkeypatch.setattr(settings, "GEMINI_API_KEY", KEY)
    monkeypatch.setattr(settings, "GEMINI_MODEL", PRIMARY)
    monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODEL", FALLBACK)
    return GeminiRecognizer()


class TestMockMode:
    async def test_mock_mode_when_no_key(self):
        recognizer = GeminiRecognizer()

        assert recognizer.mock_mode is True
        result = await recognizer.detect_food(IMAGE)
        assert result[0]["label"] == "pizza"
        assert result[0]["source"] == "mock_development"

    def test_a_key_turns_mock_mode_off(self, recognizer):
        assert recognizer.mock_mode is False

    async def test_real_mode_without_key_raises(self):
        recognizer = GeminiRecognizer(mock_mode=False)

        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            await recognizer.detect_food(IMAGE)


class TestModelSelection:
    def test_primary_then_fallback(self, recognizer):
        assert recognizer.models == [PRIMARY, FALLBACK]

    def test_duplicate_or_empty_fallback_is_ignored(self, monkeypatch):
        monkeypatch.setattr(settings, "GEMINI_MODEL", PRIMARY)
        monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODEL", PRIMARY)
        assert GeminiRecognizer().models == [PRIMARY]

        monkeypatch.setattr(settings, "GEMINI_FALLBACK_MODEL", "")
        assert GeminiRecognizer().models == [PRIMARY]


class TestRecordedResponses:
    @respx.mock
    async def test_recorded_pizza_photo(self, recognizer):
        respx.post(url(PRIMARY)).respond(200, json=recorded("pizza"))

        result = await recognizer.detect_food(IMAGE)

        assert result == [{"label": "pizza", "confidence": 0.99, "source": "gemini"}]

    @respx.mock
    async def test_recorded_photo_with_no_food_is_an_empty_list(self, recognizer):
        respx.post(url(PRIMARY)).respond(200, json=recorded("no_food"))

        assert await recognizer.detect_food(IMAGE) == []


class TestRequest:
    @respx.mock
    async def test_credential_is_in_a_header_and_never_the_url(self, recognizer):
        route = respx.post(url(PRIMARY)).respond(200, json=answer())

        await recognizer.detect_food(IMAGE)

        request = route.calls.last.request
        assert request.headers["x-goog-api-key"] == KEY
        assert KEY not in str(request.url)

    @respx.mock
    async def test_sends_the_image_with_its_mime_type_and_a_json_schema(self, recognizer):
        route = respx.post(url(PRIMARY)).respond(200, json=answer())

        await recognizer.detect_food(IMAGE, mime_type="image/png")

        body = json.loads(route.calls.last.request.content)
        assert body["contents"][0]["parts"][1]["inline_data"]["mime_type"] == "image/png"
        config = body["generationConfig"]
        assert config["responseMimeType"] == "application/json"
        assert config["responseSchema"]["required"] == ["foods"]
        assert config["temperature"] == 0


class TestFallback:
    @respx.mock
    @pytest.mark.parametrize("status", [429, 500, 503])
    async def test_retryable_status_falls_back_to_the_second_model(self, recognizer, status):
        respx.post(url(PRIMARY)).respond(status)
        fallback = respx.post(url(FALLBACK)).respond(
            200, json=answer({"name": "rice", "confidence": 0.9})
        )

        result = await recognizer.detect_food(IMAGE)

        assert result[0]["label"] == "rice"
        assert fallback.called

    @respx.mock
    async def test_network_failure_falls_back(self, recognizer):
        respx.post(url(PRIMARY)).mock(side_effect=httpx.ConnectTimeout("timed out"))
        respx.post(url(FALLBACK)).respond(200, json=answer({"name": "rice", "confidence": 0.9}))

        assert (await recognizer.detect_food(IMAGE))[0]["label"] == "rice"

    @respx.mock
    async def test_both_models_limited_fails_closed(self, recognizer):
        respx.post(url(PRIMARY)).respond(429)
        respx.post(url(FALLBACK)).respond(429)

        with pytest.raises(FoodRecognitionError):
            await recognizer.detect_food(IMAGE)

    @respx.mock
    @pytest.mark.parametrize("status", [400, 401, 403, 404])
    async def test_client_errors_do_not_fall_back(self, recognizer, status):
        respx.post(url(PRIMARY)).respond(status)
        fallback = respx.post(url(FALLBACK)).respond(200, json=answer())

        with pytest.raises(FoodRecognitionError):
            await recognizer.detect_food(IMAGE)

        assert not fallback.called

    @respx.mock
    async def test_a_failure_never_exposes_the_key(self, recognizer):
        respx.post(url(PRIMARY)).respond(403)

        with pytest.raises(FoodRecognitionError) as raised:
            await recognizer.detect_food(IMAGE)

        error: BaseException | None = raised.value
        while error is not None:
            assert KEY not in str(error)
            error = error.__cause__


class TestParsing:
    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"candidates": []},
            {"promptFeedback": {"blockReason": "SAFETY"}},
        ],
    )
    def test_a_blocked_or_empty_response_is_a_failure_not_no_food(self, recognizer, data):
        with pytest.raises(FoodRecognitionError):
            recognizer._parse(data)

    @pytest.mark.parametrize("text", ["not json", "[]", '{"foods": "pizza"}', '{"other": []}', ""])
    def test_malformed_output_is_a_failure(self, recognizer, text):
        data = {"candidates": [{"content": {"parts": [{"text": text}]}}]}

        with pytest.raises(FoodRecognitionError):
            recognizer._parse(data)

    def test_names_are_normalised_and_length_limited(self, recognizer):
        result = recognizer._parse(
            answer({"name": "  Pepperoni   PIZZA ", "confidence": 0.9},
                   {"name": "x" * 500, "confidence": 0.5})
        )

        assert result[0]["label"] == "pepperoni pizza"
        assert len(result[1]["label"]) == GeminiRecognizer.MAX_NAME_LENGTH

    def test_confidence_is_clamped_to_the_unit_interval(self, recognizer):
        result = recognizer._parse(
            answer({"name": "a", "confidence": 7}, {"name": "b", "confidence": -1})
        )

        assert {p["label"]: p["confidence"] for p in result} == {"a": 1.0, "b": 0.0}

    def test_duplicates_keep_the_highest_confidence(self, recognizer):
        result = recognizer._parse(
            answer({"name": "Rice", "confidence": 0.4}, {"name": "rice", "confidence": 0.8})
        )

        assert result == [{"label": "rice", "confidence": 0.8, "source": "gemini"}]

    def test_ranked_by_confidence_and_capped(self, recognizer):
        foods = [{"name": f"food {i}", "confidence": i / 10} for i in range(1, 7)]

        result = recognizer._parse(answer(*foods))

        assert [p["label"] for p in result] == ["food 6", "food 5", "food 4"]

    @pytest.mark.parametrize(
        "item",
        [
            "pizza",
            {"name": 5, "confidence": 0.9},
            {"name": "", "confidence": 0.9},
            {"name": "   ", "confidence": 0.9},
            {"name": "pizza", "confidence": "high"},
            {"name": "pizza", "confidence": True},
            {"name": "pizza"},
        ],
    )
    def test_invalid_items_are_skipped(self, recognizer, item):
        assert recognizer._parse(answer(item)) == []
