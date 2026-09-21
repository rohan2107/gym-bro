"""Tests for the USDA FoodData Central nutrition service.

tests/fixtures/usda/banana_search.json is a real search response (query "banana, raw", recorded
2026-09-21), trimmed to the fields the service reads. It matters because real Foundation and SR
Legacy results list Energy twice, in kJ and kcal, in either order.

Nothing here makes a live call.
"""

import json
import logging
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from app.config import settings
from app.services.nutrition import (
    NutritionLookupError,
    NutritionService,
    estimate_to_nutrition,
    scale_to_portion,
)

FIXTURES = Path(__file__).parent / "fixtures" / "usda"
SEARCH_URL = f"{NutritionService.BASE_URL}/foods/search"
KEY = "test-usda-key-do-not-leak"


def app_log_text(caplog) -> str:
    """Log lines written by this app (the HTTP client's own INFO lines are quieted in create_app)."""
    return "\n".join(r.getMessage() for r in caplog.records if r.name.startswith("app."))


def recorded_banana() -> dict[str, Any]:
    return json.loads((FIXTURES / "banana_search.json").read_text())


def food(fdc_id: int, description: str, data_type: str = "Survey (FNDDS)", energy: float = 100) -> dict[str, Any]:
    return {
        "fdcId": fdc_id,
        "description": description,
        "dataType": data_type,
        "foodNutrients": [
            {"nutrientName": "Energy", "unitName": "KCAL", "value": energy},
            {"nutrientName": "Protein", "unitName": "G", "value": 1.0},
            {"nutrientName": "Carbohydrate, by difference", "unitName": "G", "value": 20.0},
            {"nutrientName": "Total lipid (fat)", "unitName": "G", "value": 0.5},
        ],
    }


@pytest.fixture
def nutrition_service(monkeypatch) -> NutritionService:
    """A real-mode service with a fake key and no retry delay."""
    monkeypatch.setattr(settings, "USDA_API_KEY", KEY)
    monkeypatch.setattr(NutritionService, "RETRY_DELAY_SECONDS", 0)
    return NutritionService(mock_mode=False)


class TestMockMode:
    async def test_returns_fixed_data_without_a_key(self):
        result = await NutritionService().search_food("pizza")

        assert result is not None
        assert result["confidence"] == "mock"

    async def test_lookup_by_fdc_id_is_mocked_too(self):
        result = await NutritionService().lookup_by_fdc_id(123)

        assert result is not None
        assert result["fdc_id"] == 123


class TestSearchRequest:
    @respx.mock
    async def test_credential_is_a_header_and_never_in_the_url(self, nutrition_service):
        route = respx.get(SEARCH_URL).respond(200, json={"foods": [food(1, "Pizza, cheese")]})

        await nutrition_service.search_food("pizza")

        request = route.calls.last.request
        assert request.headers["x-api-key"] == KEY
        assert KEY not in str(request.url)
        assert "api_key" not in str(request.url)

    @respx.mock
    async def test_sends_no_datatype_filter(self, nutrition_service):
        """Any filter containing "Survey (FNDDS)" made USDA answer 400 about half the time."""
        route = respx.get(SEARCH_URL).respond(200, json={"foods": [food(1, "Pizza, cheese")]})

        await nutrition_service.search_food("pizza")

        params = route.calls.last.request.url.params
        assert "dataType" not in params
        assert params["query"] == "pizza"
        assert params["pageSize"] == "25"


class TestSearchResults:
    @respx.mock
    async def test_returns_nutrition_per_100g(self, nutrition_service):
        respx.get(SEARCH_URL).respond(
            200, json={"foods": [food(174987, "Pizza, cheese, regular crust", energy=265)]}
        )

        result = await nutrition_service.search_food("pizza, cheese, regular crust")

        assert result == {
            "name": "Pizza, cheese, regular crust",
            "fdc_id": 174987,
            "calories": 265,
            "protein_g": 1.0,
            "carbs_g": 20.0,
            "fat_g": 0.5,
            "serving_size": "100g",
            "confidence": "high",
        }

    @respx.mock
    async def test_recorded_banana_search_picks_plain_raw_banana(self, nutrition_service):
        respx.get(SEARCH_URL).respond(200, json=recorded_banana())

        result = await nutrition_service.search_food("banana")

        assert result is not None
        assert result["name"] == "Banana, raw"
        assert result["calories"] == 97

    @respx.mock
    async def test_nothing_anywhere_is_none_after_widening_once(self, nutrition_service):
        route = respx.get(SEARCH_URL).respond(200, json={"foods": []})

        assert await nutrition_service.search_food("nonexistentfood123") is None

        sizes = [call.request.url.params["pageSize"] for call in route.calls]
        assert sizes == ["25", "50"]

    @respx.mock
    async def test_widens_the_search_when_a_small_page_has_no_usable_result(self, nutrition_service):
        """Branded products can fill the first page; the wider page reaches a real food."""
        branded = food(1, "PEPPERONI PIZZA", "Branded")
        route = respx.get(SEARCH_URL).mock(
            side_effect=[
                httpx.Response(200, json={"foods": [branded]}),
                httpx.Response(200, json={"foods": [branded, food(2, "Pizza with pepperoni")]}),
            ]
        )

        result = await nutrition_service.search_food("pepperoni pizza")

        assert result is not None and result["name"] == "Pizza with pepperoni"
        assert route.call_count == 2

    @respx.mock
    async def test_a_usable_first_page_is_not_widened(self, nutrition_service):
        route = respx.get(SEARCH_URL).respond(200, json={"foods": [food(1, "Banana, raw")]})

        await nutrition_service.search_food("banana")

        assert route.call_count == 1

    @respx.mock
    async def test_branded_products_are_never_used(self, nutrition_service):
        respx.get(SEARCH_URL).respond(200, json={"foods": [food(1, "BANANA", "Branded")]})

        assert await nutrition_service.search_food("banana") is None

    @respx.mock
    async def test_an_entry_with_no_macro_data_is_skipped(self, nutrition_service):
        """A recorded Foundation chicken lunchmeat had 71 nutrients and none of the four macros."""
        empty = {
            "fdcId": 1,
            "description": "Lunchmeat, chicken breast, sliced",
            "dataType": "Foundation",
            "foodNutrients": [{"nutrientName": "Vitamin C", "unitName": "MG", "value": 0}],
        }
        respx.get(SEARCH_URL).respond(
            200, json={"foods": [empty, food(2, "Chicken breast, rotisserie", energy=144)]}
        )

        result = await nutrition_service.search_food("chicken breast")

        assert result is not None
        assert result["name"] == "Chicken breast, rotisserie"


class TestFailures:
    @respx.mock
    async def test_a_transient_400_is_retried(self, nutrition_service):
        route = respx.get(SEARCH_URL).mock(
            side_effect=[
                httpx.Response(400, text="<html>400 Bad Request</html>"),
                httpx.Response(200, json={"foods": [food(1, "Banana, raw")]}),
            ]
        )

        result = await nutrition_service.search_food("banana")

        assert result is not None
        assert route.call_count == 2

    @respx.mock
    async def test_errors_on_the_small_page_still_reach_the_wider_search(self, nutrition_service):
        route = respx.get(SEARCH_URL).mock(
            side_effect=[
                httpx.Response(400),
                httpx.Response(400),
                httpx.Response(200, json={"foods": [food(1, "Banana, raw")]}),
            ]
        )

        result = await nutrition_service.search_food("banana")

        assert result is not None
        assert route.calls.last.request.url.params["pageSize"] == "50"

    @respx.mock
    @pytest.mark.parametrize("status", [400, 500, 503])
    async def test_repeated_errors_raise_instead_of_looking_like_no_match(
        self, nutrition_service, status
    ):
        route = respx.get(SEARCH_URL).respond(status)

        with pytest.raises(NutritionLookupError):
            await nutrition_service.search_food("banana")

        assert route.call_count == 4  # two page sizes, two attempts each

    @respx.mock
    @pytest.mark.parametrize("status", [401, 403, 429])
    async def test_a_bad_key_or_rate_limit_is_not_retried(self, nutrition_service, status):
        route = respx.get(SEARCH_URL).respond(status)

        with pytest.raises(NutritionLookupError):
            await nutrition_service.search_food("banana")

        assert route.call_count == 1

    @respx.mock
    async def test_network_failure_raises(self, nutrition_service):
        respx.get(SEARCH_URL).mock(side_effect=httpx.ConnectTimeout("timed out"))

        with pytest.raises(NutritionLookupError):
            await nutrition_service.search_food("banana")

    @respx.mock
    async def test_a_non_json_success_body_is_treated_as_a_failure(self, nutrition_service):
        respx.get(SEARCH_URL).respond(200, text="<html>not json</html>")

        with pytest.raises(NutritionLookupError):
            await nutrition_service.search_food("banana")

    @respx.mock
    async def test_failures_never_log_or_raise_the_key_or_url(self, nutrition_service, caplog):
        respx.get(SEARCH_URL).respond(400)
        caplog.set_level(logging.DEBUG)

        with pytest.raises(NutritionLookupError) as raised:
            await nutrition_service.search_food("banana")

        assert KEY not in caplog.text
        assert "api.nal.usda.gov" not in app_log_text(caplog)
        assert KEY not in str(raised.value)
        assert "api.nal.usda.gov" not in str(raised.value)
        assert raised.value.__cause__ is None


class TestBestMatch:
    """USDA's own order puts "Dessert pizza" ahead of pizza; the service picks a plain match."""

    @pytest.mark.parametrize(
        ("query", "candidates", "expected"),
        [
            ("apples", ["Apple, candied", "Apple, dried", "Apple, raw"], "Apple, raw"),
            ("banana", ["Banana, baked", "Banana, raw", "Peppers, banana, raw"], "Banana, raw"),
            (
                "pizza, cheese, regular crust",
                ["Dessert pizza", "Pizza, cheese, regular crust", "Pizza, cheese, thick crust"],
                "Pizza, cheese, regular crust",
            ),
            ("pepperoni pizza", ["Pizza, cheese", "Pizza with pepperoni, thin crust"], "Pizza with pepperoni, thin crust"),
            # A lunchmeat that merely contains the words loses to the food itself.
            (
                "chicken breast",
                ["Lunchmeat, chicken breast, sliced", "Chicken breast, rotisserie, skin not eaten"],
                "Chicken breast, rotisserie, skin not eaten",
            ),
        ],
    )
    def test_prefers_the_plainest_on_topic_result(self, query, candidates, expected):
        foods = [food(i, description) for i, description in enumerate(candidates)]

        assert NutritionService._best_match(query, foods)["description"] == expected

    def test_prefers_the_better_data_type_on_a_tie(self):
        foods = [food(1, "Bananas, raw", "SR Legacy"), food(2, "Banana, raw", "Survey (FNDDS)")]

        assert NutritionService._best_match("banana", foods)["fdcId"] == 2

    def test_a_close_match_on_most_of_the_words_is_accepted(self):
        """The mapped pizza query has no exact entry; three of its four words is close enough."""
        foods = [food(1, "Pizza, cheese, stuffed crust")]

        assert NutritionService._best_match("pizza, cheese, regular crust", foods) is not None

    def test_no_match_is_better_than_a_wrong_one(self):
        """Half the words is not enough: "Avocado dressing" is not avocado toast."""
        foods = [food(1, "Avocado dressing"), food(2, "Oil, avocado")]

        assert NutritionService._best_match("avocado toast", foods) is None

    def test_an_empty_query_matches_nothing(self):
        assert NutritionService._best_match("  ", [food(1, "Banana, raw")]) is None


class TestExtractNutrition:
    def test_complete_data(self, nutrition_service):
        result = nutrition_service._extract_nutrition(food(12345, "Test Food", energy=200))

        assert result["name"] == "Test Food"
        assert result["fdc_id"] == 12345
        assert result["calories"] == 200
        assert result["confidence"] == "high"

    def test_missing_nutrients_default_to_zero_and_medium_confidence(self, nutrition_service):
        result = nutrition_service._extract_nutrition(
            {"fdcId": 1, "description": "Incomplete Food", "dataType": "Branded", "foodNutrients": []}
        )

        assert (result["calories"], result["protein_g"], result["carbs_g"], result["fat_g"]) == (0, 0, 0, 0)
        assert result["confidence"] == "medium"

    def test_energy_is_taken_in_kcal_whichever_order_the_units_come_in(self, nutrition_service):
        """Recorded Foundation and SR Legacy data list kJ and kcal in either order."""
        by_name = {f["description"]: f for f in recorded_banana()["foods"]}

        kcal_first = nutrition_service._extract_nutrition(by_name["Bananas, overripe, raw"])
        kj_first = nutrition_service._extract_nutrition(by_name["Bananas, raw"])

        assert kcal_first["calories"] == 85
        assert kj_first["calories"] == 89

    def test_energy_is_never_reported_in_kilojoules(self, nutrition_service):
        result = nutrition_service._extract_nutrition(
            {
                "fdcId": 1,
                "description": "kJ only",
                "foodNutrients": [{"nutrientName": "Energy", "unitName": "kJ", "value": 371}],
            }
        )

        assert result["calories"] == 0

    def test_accepts_the_atwater_energy_name_used_by_some_foundation_foods(self, nutrition_service):
        result = nutrition_service._extract_nutrition(
            {
                "fdcId": 1,
                "description": "Peppers",
                "foodNutrients": [
                    {"nutrientName": "Energy (Atwater General Factors)", "unitName": "KCAL", "value": 23.9}
                ],
            }
        )

        assert result["calories"] == 23.9


class TestLookupByFdcId:
    @respx.mock
    async def test_success_uses_a_header_credential(self, nutrition_service):
        route = respx.get(f"{NutritionService.BASE_URL}/food/174987").respond(
            200, json=food(174987, "Pizza, cheese, regular crust", energy=265)
        )

        result = await nutrition_service.lookup_by_fdc_id(174987)

        assert result is not None
        assert result["name"] == "Pizza, cheese, regular crust"
        request = route.calls.last.request
        assert request.headers["x-api-key"] == KEY
        assert KEY not in str(request.url)

    @respx.mock
    async def test_failure_returns_none_without_logging_the_key(self, nutrition_service, caplog):
        respx.get(f"{NutritionService.BASE_URL}/food/999999").respond(404)
        caplog.set_level(logging.DEBUG)

        assert await nutrition_service.lookup_by_fdc_id(999999) is None

        assert KEY not in caplog.text
        assert "api.nal.usda.gov" not in app_log_text(caplog)


class TestBatchSearch:
    @respx.mock
    async def test_a_failing_search_becomes_none_without_sinking_the_rest(self, nutrition_service):
        respx.get(SEARCH_URL, params={"query": "bad"}).respond(403)
        respx.get(SEARCH_URL, params={"query": "rice"}).respond(200, json={"foods": [food(1, "Rice, cooked")]})

        results = await nutrition_service.batch_search(["rice", "bad"])

        assert results[0] is not None and results[0]["name"] == "Rice, cooked"
        assert results[1] is None


class TestFoodMapping:
    def test_mapped_food(self, nutrition_service):
        assert nutrition_service.get_food_mapping("burger") == "hamburger, plain"

    def test_unmapped_food_returns_itself(self, nutrition_service):
        assert nutrition_service.get_food_mapping("unknownfood") == "unknownfood"


class TestPortionHelpers:
    PER_100G = {
        "name": "Pizza, cheese",
        "fdc_id": 1,
        "calories": 265,
        "protein_g": 11.0,
        "carbs_g": 33.0,
        "fat_g": 10.0,
        "serving_size": "100g",
        "confidence": "high",
    }

    def test_scale_to_portion_scales_every_macro_and_states_the_portion(self):
        result = scale_to_portion(self.PER_100G, 250)

        assert (result["calories"], result["protein_g"], result["carbs_g"], result["fat_g"]) == (
            662,
            27.5,
            82.5,
            25.0,
        )
        assert result["serving_size"] == "250g"

    def test_scale_to_portion_keeps_the_identity_of_the_match(self):
        result = scale_to_portion(self.PER_100G, 250)

        assert (result["name"], result["fdc_id"], result["confidence"]) == ("Pizza, cheese", 1, "high")

    def test_scale_to_portion_does_not_mutate_its_input(self):
        scale_to_portion(self.PER_100G, 250)

        assert self.PER_100G["calories"] == 265

    def test_estimate_to_nutrition_has_the_same_shape_and_low_confidence(self):
        result = estimate_to_nutrition(
            "pizza", 300, {"calories": 800, "protein_g": 30.0, "carbs_g": 90.0, "fat_g": 32.0}
        )

        assert set(result) == set(self.PER_100G)
        assert result["fdc_id"] is None
        assert result["serving_size"] == "300g"
        assert result["confidence"] == "low"
