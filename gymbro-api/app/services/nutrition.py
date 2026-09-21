"""USDA FoodData Central API integration for nutrition lookup.

This service queries the USDA FoodData Central database to get nutrition information for the
foods a recognition provider found in a photo.

Two properties matter here:

* The API key is sent in the ``X-Api-Key`` header, never in the URL. httpx logs request URLs
  and puts them in exception messages, and this app logs both, so a ``?api_key=`` would put
  the credential in application logs. (It did, until this was changed.)
* "USDA has no match" and "USDA failed" are different outcomes. The first returns ``None``;
  the second raises ``NutritionLookupError``. Treating them alike showed users a misleading
  "no nutrition data" when the service had merely errored.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from ..config import settings


logger = logging.getLogger(__name__)

# Result types worth using. Branded products are excluded on purpose: their names are brand
# text and their values are label claims. FNDDS describes prepared foods the way people eat
# them; Foundation and SR Legacy cover raw ingredients.
_DATA_TYPE_RANK = {"Survey (FNDDS)": 0, "Foundation": 1, "SR Legacy": 2}

# The search endpoint intermittently answers 400 (an HTML page, not JSON) and occasionally 5xx
# to a request it answers fine a moment later, so these are retried once. 401/403 (bad key)
# and 429 (rate limited) are not: retrying cannot help.
#
# The `dataType` filter is deliberately not used. Measured 2026-09-21: with any filter that
# included "Survey (FNDDS)" about half of all requests failed with 400, at random and
# whatever the query; with no filter 45 of 45 succeeded. Types are selected in code instead.
_TRANSIENT_STATUSES = frozenset({400, 500, 502, 503, 504})

# A result must contain more than this share of the query's words to count as a match.
# "avocado toast" is not "Avocado dressing", and no match is better than a wrong one.
_MIN_WORD_OVERLAP = 0.5


class NutritionLookupError(Exception):
    """USDA could not be queried (network failure, bad key, rate limit, repeated errors).

    Not raised for "no match", which is a normal outcome and returns ``None``. The message is
    for logs, never for clients, and contains no URL.
    """


_MACRO_PREFIXES = ("Energy", "Protein", "Carbohydrate", "Total lipid", "Total fat")


def _tokens(text: str) -> set:
    """Lower-case words with a crude singular form, so "bananas" matches "Banana, raw"."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words}


class NutritionService:
    """Service for looking up nutrition data from USDA FoodData Central API."""

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    TIMEOUT_SECONDS = 8.0
    # Results requested per search. The small page is cheap (a response can be several hundred
    # KB) and usually enough; when nothing qualifies, one wider search follows, because branded
    # products can fill a small page ("pepperoni pizza" needs 50 to reach a real pizza).
    PAGE_SIZES = (25, 50)
    ATTEMPTS = 2  # per page size, for transient errors
    RETRY_DELAY_SECONDS = 0.25

    def __init__(self, mock_mode: Optional[bool] = None):
        """Initialize the USDA API client.

        Args:
            mock_mode: Force mock mode (True) or real API calls (False). When
                None, mock mode is enabled if no API key is configured.
        """
        self.api_key = settings.USDA_API_KEY or None

        if mock_mode is None:
            mock_mode = not self.api_key

        self.mock_mode = mock_mode

    async def search_food(self, query: str) -> Optional[Dict[str, Any]]:
        """Search USDA for a food and return the best match's nutrition per 100g.

        Args:
            query: Food name to search for (e.g. "banana", "pizza, cheese, regular crust").

        Returns:
            Nutrition info::

                {"name": "Banana, raw", "fdc_id": 1105073, "calories": 97,
                 "protein_g": 0.73, "carbs_g": 23, "fat_g": 0.22,
                 "serving_size": "100g", "confidence": "high"}

            or ``None`` if USDA answered and had no match.

        Raises:
            NutritionLookupError: If USDA could not be queried successfully.
        """
        # Return mock data in development/test mode
        if self.mock_mode:
            return {
                "name": f"{query.title()}, typical serving",
                "fdc_id": 999999,
                "calories": 250,
                "protein_g": 10.0,
                "carbs_g": 30.0,
                "fat_g": 10.0,
                "serving_size": "100g",
                "confidence": "mock"
            }

        answered = False
        last_status: Optional[int] = None
        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            for page_size in self.PAGE_SIZES:
                for attempt in range(self.ATTEMPTS):
                    try:
                        response = await client.get(
                            f"{self.BASE_URL}/foods/search",
                            headers={"X-Api-Key": self.api_key},
                            params={"query": query, "pageSize": page_size},
                        )
                        response.raise_for_status()
                        foods = response.json().get("foods") or []
                    except httpx.HTTPStatusError as error:
                        last_status = error.response.status_code
                        # Log the status only: the exception text carries the URL.
                        logger.warning("USDA search returned %s (attempt %d)", last_status, attempt + 1)
                        if last_status not in _TRANSIENT_STATUSES:
                            raise NutritionLookupError(f"USDA returned {last_status}") from None
                    except (httpx.TransportError, ValueError) as error:
                        logger.warning("USDA search failed: %s (attempt %d)", type(error).__name__, attempt + 1)
                    else:
                        answered = True
                        best = self._best_match(query, foods)
                        if best:
                            return self._extract_nutrition(best)
                        break  # Answered, but nothing qualified: widen the search.

                    if attempt + 1 < self.ATTEMPTS:
                        await asyncio.sleep(self.RETRY_DELAY_SECONDS)

        if answered:
            return None
        raise NutritionLookupError(
            f"USDA search failed after retries (last status {last_status})"
        )

    @staticmethod
    def _best_match(query: str, foods: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Pick the most plain, on-topic result rather than trusting USDA's first hit.

        USDA's own order puts "Dessert pizza" ahead of pizza and "Apple, candied" ahead of an
        apple, and lists a chicken-breast lunchmeat that carries no energy data at all. So:
        drop branded products and entries with no macro data, require more than half the
        query's words to appear, then prefer (in order) more matching words, a description
        that starts with a query word, fewer qualifiers, "raw", the better data type, and the
        shorter description. Returns ``None`` when nothing qualifies.

        This is a heuristic, and its accuracy is unmeasured; see docs/PHOTO_ANALYSIS.md.
        """
        wanted = _tokens(query)
        if not wanted:
            return None

        def has_macro_data(food: Dict[str, Any]) -> bool:
            names = [n.get("nutrientName", "") for n in food.get("foodNutrients", [])]
            return any(name.startswith(_MACRO_PREFIXES) for name in names)

        scored = []
        for food in foods:
            if food.get("dataType") not in _DATA_TYPE_RANK or not has_macro_data(food):
                continue
            description = food.get("description", "")
            words = _tokens(description)
            overlap = len(wanted & words) / len(wanted)
            if overlap <= _MIN_WORD_OVERLAP:
                continue
            leading = re.findall(r"[a-z0-9]+", description.lower())[:1]
            starts_on_topic = bool(leading) and next(iter(_tokens(leading[0])), "") in wanted
            scored.append((
                (
                    -overlap,
                    0 if starts_on_topic else 1,
                    len(words),
                    0 if "raw" in words else 1,
                    _DATA_TYPE_RANK[food["dataType"]],
                    len(description),
                ),
                food,
            ))
        return min(scored, key=lambda item: item[0])[1] if scored else None

    def _extract_nutrition(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract nutrition information from USDA food data.
        
        Args:
            food_data: Raw food data from USDA API
            
        Returns:
            Formatted nutrition dict
        """
        nutrients = food_data.get("foodNutrients", [])

        def value(*names: str, unit: Optional[str] = None) -> float:
            """First matching nutrient, by name in the order given and optionally by unit."""
            for name in names:
                for nutrient in nutrients:
                    if nutrient.get("nutrientName") != name:
                        continue
                    # Skip only an entry that states a different unit; one with no unit
                    # is accepted rather than dropped.
                    stated = (nutrient.get("unitName") or "").upper()
                    if unit and stated and stated != unit:
                        continue
                    return nutrient.get("value", 0)
            return 0

        return {
            "name": food_data.get("description", "Unknown food"),
            "fdc_id": food_data.get("fdcId"),
            # Foundation and SR Legacy list Energy twice, in kJ and kcal, in either order.
            # Taking "the last Energy" reported kilojoules as calories about 4x too high,
            # so the unit is matched explicitly.
            "calories": value("Energy", "Energy (Atwater General Factors)", unit="KCAL"),
            "protein_g": value("Protein"),
            "carbs_g": value("Carbohydrate, by difference", "Carbohydrate, by summation"),
            "fat_g": value("Total lipid (fat)", "Total fat (NLEA)"),
            "serving_size": "100g",  # USDA data is per 100g
            "confidence": "high" if food_data.get("dataType") == "Survey (FNDDS)" else "medium",
        }


def scale_to_portion(nutrition: Dict[str, Any], grams: float) -> Dict[str, Any]:
    """USDA's per-100g values scaled to a portion, with the portion stated in serving_size."""
    factor = grams / 100.0
    return {
        **nutrition,
        "calories": round(nutrition["calories"] * factor),
        "protein_g": round(nutrition["protein_g"] * factor, 1),
        "carbs_g": round(nutrition["carbs_g"] * factor, 1),
        "fat_g": round(nutrition["fat_g"] * factor, 1),
        "serving_size": f"{round(grams)}g",
    }


def estimate_to_nutrition(name: str, grams: float, estimate: Dict[str, Any]) -> Dict[str, Any]:
    """A model's own estimate in the same shape as a USDA result, marked as not from USDA."""
    return {
        "name": name,
        "fdc_id": None,
        **estimate,
        "serving_size": f"{round(grams)}g",
        "confidence": "low",
    }
