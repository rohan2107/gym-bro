"""Nutrition lookup against a local copy of USDA FoodData Central.

Through M0.3b this queried USDA's search API on every request. That call was unreliable (any
`dataType` filter made it fail with `400` about half the time, at random - AUDIT F16) and its
own ranking was often poor. M1.0 (ADR-0010) replaced it with a local, read-only reference
table (`UsdaFood`, populated once by an Alembic migration from data/usda_foods.json - see
scripts/build_usda_dataset.py) built from USDA's bulk downloads, which need no API key and are
public domain. The request path now makes no external call for nutrition at all.

The query itself is deliberately simple: a broad SQL prefilter (does the name contain any word
of the query?) followed by the same ranking heuristic used before, unchanged, now applied in
Python to rows from this database instead of USDA's API. At this table's size (about 13,500
foods) an unfiltered scan for even a common single word ("chicken": ~800 rows) takes single-digit
milliseconds, so there is no candidate cap to get wrong - every match reaches the ranking step.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from ..models import UsdaFood


logger = logging.getLogger(__name__)

# Result types worth using. Branded products are excluded on purpose: their names are brand
# text and their values are label claims. FNDDS describes prepared foods the way people eat
# them; Foundation and SR Legacy cover raw ingredients. (Enforced at ingestion - Branded is
# never in the table at all - kept here only for _best_match's data-type ranking.)
_DATA_TYPE_RANK = {"Survey (FNDDS)": 0, "Foundation": 1, "SR Legacy": 2}

# A result must contain more than this share of the query's words to count as a match.
# "avocado toast" is not "Avocado dressing", and no match is better than a wrong one.
_MIN_WORD_OVERLAP = 0.5

# A token shorter than this ("of", "a") is dropped before searching: matching on it would pull
# a large, meaningless share of the table for no benefit to ranking.
_MIN_TOKEN_LENGTH = 3


class NutritionLookupError(Exception):
    """The local database could not be queried (a connection or query failure).

    Not raised for "no match", which is a normal outcome and returns ``None``. Every food this
    app looks up is expected to have *some* candidate rows; a query that runs but finds nothing
    usable is not this error, only a query that could not run is.
    """


def _tokens(text: str) -> set:
    """Lower-case words with a crude singular form, so "bananas" matches "Banana, raw"."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {
        w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w
        for w in words
        if len(w) >= _MIN_TOKEN_LENGTH
    }


class NutritionService:
    """Looks up nutrition for a food name in the local USDA reference table."""

    def __init__(self, session: Session):
        self.session = session

    async def search_food(self, query: str) -> Optional[Dict[str, Any]]:
        """Find the best match for a food name and return its nutrition per 100g.

        Args:
            query: Food name to search for (e.g. "banana", "pizza, cheese, regular crust").

        Returns:
            Nutrition info::

                {"name": "Banana, raw", "fdc_id": 2709224, "calories": 97.0,
                 "protein_g": 0.74, "carbs_g": 22.7, "fat_g": 0.28,
                 "serving_size": "100g", "portion_g": 100.0, "confidence": "high"}

            or ``None`` if nothing in the table is a good enough match.

        Raises:
            NutritionLookupError: If the table could not be queried.

        This method is declared ``async`` to match the interface the endpoint awaits
        concurrently across several foods; the query itself is a synchronous SQLAlchemy call,
        consistent with the rest of the app's synchronous database sessions inside async
        handlers (audit finding O7, scheduled for M3.0 - not specific to this method).
        """
        tokens = _tokens(query)
        if not tokens:
            return None

        try:
            condition = or_(*(func.lower(UsdaFood.name).contains(token) for token in tokens))
            candidates = self.session.exec(select(UsdaFood).where(condition)).all()
        except SQLAlchemyError as error:
            raise NutritionLookupError("USDA reference table query failed") from error

        best = self._best_match(query, candidates)
        return self._to_nutrition(best) if best else None

    @staticmethod
    def _best_match(query: str, foods: List[UsdaFood]) -> Optional[UsdaFood]:
        """Pick the most plain, on-topic result rather than trusting the SQL order.

        Unchanged from the version that ranked USDA's own search results: require more than
        half the query's words to appear, then prefer (in order) more matching words, a name
        that starts with a query word, fewer qualifiers, "raw", the better data type, and the
        shorter name. Returns ``None`` when nothing qualifies.

        This is a heuristic, and its accuracy is unmeasured; see docs/PHOTO_ANALYSIS.md.
        """
        wanted = _tokens(query)
        if not wanted:
            return None

        scored = []
        for food in foods:
            words = _tokens(food.name)
            overlap = len(wanted & words) / len(wanted)
            if overlap <= _MIN_WORD_OVERLAP:
                continue
            leading = re.findall(r"[a-z0-9]+", food.name.lower())[:1]
            starts_on_topic = bool(leading) and next(iter(_tokens(leading[0])), "") in wanted
            scored.append((
                (
                    -overlap,
                    0 if starts_on_topic else 1,
                    len(words),
                    0 if "raw" in words else 1,
                    _DATA_TYPE_RANK.get(food.data_type, 3),
                    len(food.name),
                ),
                food,
            ))
        return min(scored, key=lambda item: item[0])[1] if scored else None

    @staticmethod
    def _to_nutrition(food: UsdaFood) -> Dict[str, Any]:
        return {
            "name": food.name,
            "fdc_id": food.fdc_id,
            "calories": food.calories,
            "protein_g": food.protein_g,
            "carbs_g": food.carbs_g,
            "fat_g": food.fat_g,
            "serving_size": "100g",  # the reference table stores everything per 100g
            "portion_g": 100.0,
            "confidence": "high" if food.data_type == "Survey (FNDDS)" else "medium",
        }


def scale_to_portion(nutrition: Dict[str, Any], grams: float) -> Dict[str, Any]:
    """USDA's per-100g values scaled to a portion, with the portion stated in serving_size.

    ``portion_g`` is the same value as a plain number, so the frontend can rescale the macros
    itself (dividing by it) as the user edits the portion, without parsing ``serving_size``.
    """
    factor = grams / 100.0
    return {
        **nutrition,
        "calories": round(nutrition["calories"] * factor),
        "protein_g": round(nutrition["protein_g"] * factor, 1),
        "carbs_g": round(nutrition["carbs_g"] * factor, 1),
        "fat_g": round(nutrition["fat_g"] * factor, 1),
        "serving_size": f"{round(grams)}g",
        "portion_g": grams,
    }


def estimate_to_nutrition(name: str, grams: float, estimate: Dict[str, Any]) -> Dict[str, Any]:
    """A model's own estimate in the same shape as a USDA result, marked as not from USDA."""
    return {
        "name": name,
        "fdc_id": None,
        **estimate,
        "serving_size": f"{round(grams)}g",
        "portion_g": grams,
        "confidence": "low",
    }
