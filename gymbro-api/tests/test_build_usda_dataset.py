"""Tests for scripts/build_usda_dataset.py's pure trimming logic (no network calls).

This script runs once every few months to years, when USDA issues a new release, so it will
not be exercised again for a long time after being written - exactly the code most worth
testing now. It protects against three real defects found while first building the dataset
(2026-09-22): some releases contain literal `null` entries, Foundation foods sometimes carry
only a computed Atwater energy value, and Foundation/SR Legacy list Energy in both kJ and kcal.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_usda_dataset as build  # noqa: E402


def nutrient(name: str, unit: str, amount: float) -> dict:
    return {"nutrient": {"name": name, "unitName": unit}, "amount": amount}


def usda_food(name: str = "Banana, raw", **overrides) -> dict:
    food = {
        "fdcId": 1,
        "description": name,
        "foodNutrients": [
            nutrient("Energy", "kcal", 97.0),
            nutrient("Protein", "g", 0.74),
            nutrient("Carbohydrate, by difference", "g", 22.7),
            nutrient("Total lipid (fat)", "g", 0.28),
        ],
    }
    food.update(overrides)
    return food


class TestNutrientAmount:
    def test_finds_the_named_nutrient(self):
        food = usda_food()
        assert build.nutrient_amount(food, ("Energy",), unit="kcal") == 97.0

    def test_falls_back_through_the_name_list_in_order(self):
        food = usda_food(foodNutrients=[nutrient("Carbohydrate, by summation", "g", 14.3)])

        amount = build.nutrient_amount(food, build.CARB_NAMES)

        assert amount == 14.3

    def test_a_missing_nutrient_returns_none(self):
        food = usda_food(foodNutrients=[])
        assert build.nutrient_amount(food, ("Energy",), unit="kcal") is None

    def test_unit_mismatch_is_not_a_match(self):
        """Foundation and SR Legacy list Energy in both kJ and kcal; asking for kcal must
        never return the kJ value (about 4x too large)."""
        food = usda_food(foodNutrients=[nutrient("Energy", "kJ", 405.0)])

        assert build.nutrient_amount(food, ("Energy",), unit="kcal") is None

    def test_prefers_plain_energy_over_atwater_when_both_are_present(self):
        food = usda_food(foodNutrients=[
            nutrient("Energy", "kcal", 97.0),
            nutrient("Energy (Atwater General Factors)", "kcal", 89.0),
        ])

        assert build.nutrient_amount(food, build.ENERGY_NAMES, unit="kcal") == 97.0

    def test_falls_back_to_atwater_general_then_specific(self):
        """Some Foundation foods carry no directly measured Energy, only computed values."""
        general_only = usda_food(foodNutrients=[nutrient("Energy (Atwater General Factors)", "kcal", 61.8)])
        specific_only = usda_food(foodNutrients=[nutrient("Energy (Atwater Specific Factors)", "kcal", 55.6)])

        assert build.nutrient_amount(general_only, build.ENERGY_NAMES, unit="kcal") == 61.8
        assert build.nutrient_amount(specific_only, build.ENERGY_NAMES, unit="kcal") == 55.6


class TestTrim:
    def test_keeps_a_usable_food(self):
        result = build.trim(usda_food(), "Survey (FNDDS)")

        assert result == {
            "fdc_id": 1,
            "name": "Banana, raw",
            "data_type": "Survey (FNDDS)",
            "calories": 97.0,
            "protein_g": 0.74,
            "carbs_g": 22.7,
            "fat_g": 0.28,
        }

    def test_drops_a_food_with_no_kcal_energy_at_all(self):
        """Observed in the 2026-04-30 Foundation release: 42 of 363 foods."""
        food = usda_food(foodNutrients=[nutrient("Energy", "kJ", 405.0)])

        assert build.trim(food, "Foundation") is None

    @pytest.mark.parametrize("description", [None, "", "   "])
    def test_drops_a_food_with_no_usable_name(self, description):
        assert build.trim(usda_food(description=description), "Foundation") is None

    def test_missing_macros_default_to_zero_rather_than_dropping_the_food(self):
        food = usda_food(foodNutrients=[nutrient("Energy", "kcal", 97.0)])

        result = build.trim(food, "Survey (FNDDS)")

        assert (result["protein_g"], result["carbs_g"], result["fat_g"]) == (0.0, 0.0, 0.0)

    def test_rounds_values_for_compactness(self):
        food = usda_food(foodNutrients=[
            nutrient("Energy", "kcal", 96.987),
            nutrient("Protein", "g", 0.7351),
        ])

        result = build.trim(food, "Survey (FNDDS)")

        assert (result["calories"], result["protein_g"]) == (97.0, 0.74)


class TestNullEntriesInSource:
    def test_literal_null_entries_in_a_release_are_skipped(self):
        """Observed in the 2026-04-30 Foundation release: 32 of 395 entries were `null`, not
        dicts with missing fields - the raw JSON array itself contained nulls."""
        raw = [usda_food(), None, usda_food(name="Apple, raw")]

        foods = [f for f in raw if f is not None]

        assert len(foods) == 2
