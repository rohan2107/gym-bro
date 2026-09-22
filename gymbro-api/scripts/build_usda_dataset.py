#!/usr/bin/env python3
"""Builds data/usda_foods.json from USDA FoodData Central's bulk downloads.

Run this once per refresh (FNDDS every two years, Foundation twice a year; see
docs/adr/0010-usda-as-a-local-reference.md), not on every deploy. It downloads the three
JSON releases pinned below, trims each food to what the app uses, and writes one committed
file plus a manifest recording exactly where the data came from.

    cd gymbro-api && .venv/bin/python scripts/build_usda_dataset.py

Branded Foods is deliberately excluded: its names are brand text and its values are label
claims, not measurements (this matches NutritionService's existing exclusion of "Branded"
results, applied here at ingestion instead of at query time).

Data source: USDA FoodData Central (fdc.nal.usda.gov), U.S. Department of Agriculture,
Agricultural Research Service. Public domain (CC0 1.0), per
https://fdc.nal.usda.gov/api-guide - "FoodData Central data are in the public domain, and
there are no restrictions on their use." Users are asked, not required, to credit FoodData
Central as the source.
"""

import json
import sys
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

BASE_URL = "https://fdc.nal.usda.gov/fdc-datasets"
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "usda_foods.json"

# Pinned to a specific dated release each, not "latest": reproducibility matters more than
# freshness for data that changes every few months to years. Bump these deliberately.
RELEASES = [
    {
        "label": "Foundation",
        "file": "FoodData_Central_foundation_food_json_2026-04-30.zip",
        "top_key": "FoundationFoods",
        "release_date": "2026-04-30",
    },
    {
        "label": "Survey (FNDDS)",
        "file": "FoodData_Central_survey_food_json_2024-10-31.zip",
        "top_key": "SurveyFoods",
        "release_date": "2024-10-31",
    },
    {
        "label": "SR Legacy",
        "file": "FoodData_Central_sr_legacy_food_json_2018-04.zip",
        "top_key": "SRLegacyFoods",
        "release_date": "2018-04",
    },
]

# In priority order: the first that is present and in kcal is used. Foundation foods
# sometimes carry only a computed Atwater energy value rather than a directly measured one.
ENERGY_NAMES = ("Energy", "Energy (Atwater General Factors)", "Energy (Atwater Specific Factors)")
CARB_NAMES = ("Carbohydrate, by difference", "Carbohydrate, by summation")
FAT_NAMES = ("Total lipid (fat)", "Total fat (NLEA)")


def download_release(release: Dict[str, str]) -> List[Optional[Dict[str, Any]]]:
    url = f"{BASE_URL}/{release['file']}"
    print(f"Downloading {release['label']}: {url}")
    response = httpx.get(url, timeout=120.0, follow_redirects=True)
    response.raise_for_status()
    with zipfile.ZipFile(BytesIO(response.content)) as archive:
        json_names = [n for n in archive.namelist() if n.endswith(".json")]
        if len(json_names) != 1:
            raise RuntimeError(f"Expected one JSON file in {release['file']}, found {json_names}")
        with archive.open(json_names[0]) as fh:
            data = json.load(fh)
    return data[release["top_key"]]


def nutrient_amount(food: Dict[str, Any], names: tuple, unit: Optional[str] = None) -> Optional[float]:
    """The amount of the first matching nutrient, by name in priority order."""
    for name in names:
        for entry in food.get("foodNutrients", []):
            nutrient = entry.get("nutrient") or {}
            if nutrient.get("name") != name:
                continue
            if unit and (nutrient.get("unitName") or "").lower() != unit:
                continue
            amount = entry.get("amount")
            if amount is not None:
                return float(amount)
    return None


def trim(food: Dict[str, Any], data_type: str) -> Optional[Dict[str, Any]]:
    """One food, reduced to what NutritionService needs, or None if it has no usable energy."""
    description = food.get("description")
    calories = nutrient_amount(food, ENERGY_NAMES, unit="kcal")
    if not isinstance(description, str) or not description.strip() or calories is None:
        return None
    return {
        "fdc_id": food["fdcId"],
        "name": description,
        "data_type": data_type,
        "calories": round(calories, 1),
        "protein_g": round(nutrient_amount(food, ("Protein",)) or 0.0, 2),
        "carbs_g": round(nutrient_amount(food, CARB_NAMES) or 0.0, 2),
        "fat_g": round(nutrient_amount(food, FAT_NAMES) or 0.0, 2),
    }


def main() -> None:
    all_foods: List[Dict[str, Any]] = []
    counts: Dict[str, Dict[str, int]] = {}

    for release in RELEASES:
        raw = download_release(release)
        # A small number of entries in some releases are literally `null` (observed in the
        # 2026-04-30 Foundation release: 32 of 395). Not a parsing bug - the source data has
        # them.
        foods = [f for f in raw if f is not None]
        trimmed = [t for f in foods if (t := trim(f, release["label"])) is not None]
        all_foods.extend(trimmed)
        counts[release["label"]] = {
            "downloaded": len(raw),
            "null_in_source": len(raw) - len(foods),
            "no_usable_energy": len(foods) - len(trimmed),
            "kept": len(trimmed),
        }
        print(f"  {release['label']}: {counts[release['label']]}")

    fdc_ids = [f["fdc_id"] for f in all_foods]
    assert len(fdc_ids) == len(set(fdc_ids)), "fdc_id collision across releases"

    output = {
        "manifest": {
            "source": "USDA FoodData Central (fdc.nal.usda.gov), U.S. Department of Agriculture, "
            "Agricultural Research Service",
            "license": "Public domain (CC0 1.0); FoodData Central credited as the source",
            "excluded": "Branded Foods (brand text and label claims, not measurements)",
            "releases": RELEASES,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "scripts/build_usda_dataset.py",
            "counts": counts,
            "total_foods": len(all_foods),
        },
        "foods": all_foods,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(output, indent=1) + "\n")
    print(f"\nWrote {len(all_foods)} foods to {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    sys.exit(main())
