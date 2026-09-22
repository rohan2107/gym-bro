"""Tests for nutrition lookup against the local USDA reference table (see ADR-0010).

The `session` fixture (conftest.py) gives a real, empty SQLite database with every model's
table created; these tests seed a handful of representative UsdaFood rows rather than the full
~13,500-row dataset that ships in production, so they run fast and do not depend on a
particular USDA release's exact contents.
"""

from typing import Any, Dict

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models import UsdaFood
from app.services.nutrition import (
    NutritionLookupError,
    NutritionService,
    estimate_to_nutrition,
    scale_to_portion,
)


def food(
    fdc_id: int,
    name: str,
    data_type: str = "Survey (FNDDS)",
    calories: float = 100.0,
    protein_g: float = 1.0,
    carbs_g: float = 20.0,
    fat_g: float = 0.5,
) -> UsdaFood:
    return UsdaFood(
        fdc_id=fdc_id,
        name=name,
        data_type=data_type,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
    )


def seed(session, *foods: UsdaFood) -> None:
    for f in foods:
        session.add(f)
    session.commit()


@pytest.fixture
def nutrition_service(session) -> NutritionService:
    return NutritionService(session)


class TestSearchFood:
    async def test_finds_an_exact_name(self, session, nutrition_service):
        seed(session, food(1, "Banana, raw", calories=97.0, protein_g=0.74, carbs_g=22.7, fat_g=0.28))

        result = await nutrition_service.search_food("banana")

        assert result == {
            "name": "Banana, raw",
            "fdc_id": 1,
            "calories": 97.0,
            "protein_g": 0.74,
            "carbs_g": 22.7,
            "fat_g": 0.28,
            "serving_size": "100g",
            "portion_g": 100.0,
            "confidence": "high",
        }

    async def test_matches_the_singular_query_against_a_plural_name(self, session, nutrition_service):
        seed(session, food(1, "Bananas, ripe and slightly ripe, raw"))

        assert await nutrition_service.search_food("banana") is not None

    async def test_prefers_the_plainest_on_topic_result_over_a_decoy(self, session, nutrition_service):
        """USDA-style data routinely lists a garnish or dessert ahead of the plain food."""
        seed(
            session,
            food(1, "Dessert pizza"),
            food(2, "Pizza, cheese, regular crust"),
            food(3, "Pizza, cheese, thick crust"),
        )

        result = await nutrition_service.search_food("pizza, cheese, regular crust")

        assert result["name"] == "Pizza, cheese, regular crust"

    async def test_no_match_returns_none_without_raising(self, session, nutrition_service):
        seed(session, food(1, "Banana, raw"))

        assert await nutrition_service.search_food("xyzzy") is None

    async def test_no_rows_in_the_table_at_all_returns_none(self, session, nutrition_service):
        assert await nutrition_service.search_food("banana") is None

    async def test_a_query_of_only_short_words_finds_nothing_rather_than_matching_everything(
        self, session, nutrition_service
    ):
        """"of" and "a" are dropped as tokens, so a query made only of them must not become an
        unfiltered scan that matches the whole table."""
        seed(session, food(1, "Banana, raw"), food(2, "Apple, raw"))

        assert await nutrition_service.search_food("a of") is None

    async def test_db_failure_raises_lookup_error_not_a_silent_none(self, session, nutrition_service, monkeypatch):
        def broken_exec(*args, **kwargs):
            raise SQLAlchemyError("connection lost")

        monkeypatch.setattr(session, "exec", broken_exec)

        with pytest.raises(NutritionLookupError):
            await nutrition_service.search_food("banana")


class TestBestMatch:
    """USDA-style data's own order is not always sensible; the service ranks it."""

    @pytest.mark.parametrize(
        ("query", "names", "expected"),
        [
            ("apples", ["Apple, candied", "Apple, dried", "Apple, raw"], "Apple, raw"),
            ("banana", ["Banana, baked", "Banana, raw", "Peppers, banana, raw"], "Banana, raw"),
            (
                "pizza, cheese, regular crust",
                ["Dessert pizza", "Pizza, cheese, regular crust", "Pizza, cheese, thick crust"],
                "Pizza, cheese, regular crust",
            ),
            (
                "pepperoni pizza",
                ["Pizza, cheese", "Pizza with pepperoni, thin crust"],
                "Pizza with pepperoni, thin crust",
            ),
        ],
    )
    def test_prefers_the_plainest_on_topic_result(self, query, names, expected):
        foods = [food(i, name) for i, name in enumerate(names)]

        assert NutritionService._best_match(query, foods).name == expected

    def test_prefers_the_better_data_type_on_a_tie(self):
        foods = [food(1, "Bananas, raw", "SR Legacy"), food(2, "Banana, raw", "Survey (FNDDS)")]

        assert NutritionService._best_match("banana", foods).fdc_id == 2

    def test_a_close_match_on_most_of_the_words_is_accepted(self):
        foods = [food(1, "Pizza, cheese, stuffed crust")]

        assert NutritionService._best_match("pizza, cheese, regular crust", foods) is not None

    def test_no_match_is_better_than_a_wrong_one(self):
        """Half the words is not enough: "Avocado dressing" is not avocado toast."""
        foods = [food(1, "Avocado dressing"), food(2, "Oil, avocado")]

        assert NutritionService._best_match("avocado toast", foods) is None

    def test_an_empty_query_matches_nothing(self):
        assert NutritionService._best_match("  ", [food(1, "Banana, raw")]) is None

    def test_an_empty_candidate_list_matches_nothing(self):
        assert NutritionService._best_match("banana", []) is None


class TestToNutrition:
    def test_survey_fndds_is_reported_as_high_confidence(self):
        result = NutritionService._to_nutrition(food(1, "Banana, raw", "Survey (FNDDS)"))
        assert result["confidence"] == "high"

    @pytest.mark.parametrize("data_type", ["Foundation", "SR Legacy"])
    def test_other_data_types_are_reported_as_medium_confidence(self, data_type):
        result = NutritionService._to_nutrition(food(1, "Banana, raw", data_type))
        assert result["confidence"] == "medium"

    def test_values_are_reported_per_100g(self):
        result = NutritionService._to_nutrition(food(1, "Banana, raw"))
        assert (result["serving_size"], result["portion_g"]) == ("100g", 100.0)


class TestPortionHelpers:
    PER_100G: Dict[str, Any] = {
        "name": "Pizza, cheese",
        "fdc_id": 1,
        "calories": 265,
        "protein_g": 11.0,
        "carbs_g": 33.0,
        "fat_g": 10.0,
        "serving_size": "100g",
        "portion_g": 100.0,
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
        assert result["portion_g"] == 250

    def test_scale_to_portion_keeps_the_identity_of_the_match(self):
        result = scale_to_portion(self.PER_100G, 250)

        assert (result["name"], result["fdc_id"], result["confidence"]) == ("Pizza, cheese", 1, "high")

    def test_scale_to_portion_does_not_mutate_its_input(self):
        scale_to_portion(self.PER_100G, 250)

        assert self.PER_100G["calories"] == 265

    def test_scaling_again_from_the_original_100g_values_is_exact(self):
        """The frontend rescales a portion by re-deriving from the per-100g basis, not by
        compounding an already-scaled result; scale_to_portion must support being called
        again from PER_100G for a different grams value without drift."""
        first = scale_to_portion(self.PER_100G, 250)
        second = scale_to_portion(self.PER_100G, 400)

        assert first["calories"] != second["calories"]
        assert second["calories"] == round(265 * 4)

    def test_estimate_to_nutrition_has_the_same_shape_and_low_confidence(self):
        result = estimate_to_nutrition(
            "pizza", 300, {"calories": 800, "protein_g": 30.0, "carbs_g": 90.0, "fat_g": 32.0}
        )

        assert set(result) == set(self.PER_100G)
        assert result["fdc_id"] is None
        assert result["serving_size"] == "300g"
        assert result["portion_g"] == 300
        assert result["confidence"] == "low"
