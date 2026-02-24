"""USDA FoodData Central API integration for nutrition lookup.

This service queries the USDA FoodData Central database to get
nutrition information for food items detected by the Vision API.
"""

import logging
import os
from typing import Any, Dict, List, Optional
import httpx


logger = logging.getLogger(__name__)


class NutritionService:
    """Service for looking up nutrition data from USDA FoodData Central API."""

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    def __init__(self, mock_mode: Optional[bool] = None):
        """Initialize the USDA API client.
        
        Args:
            mock_mode: Force mock mode (True) or prod mode (False).
                      If None, auto-detect based on API key presence.
        """
        self.api_key = os.getenv("USDA_API_KEY")
        
        # Auto-detect mock mode if not explicitly set
        if mock_mode is None:
            mock_mode = not self.api_key
        
        self.mock_mode = mock_mode
        
        if not mock_mode and not self.api_key:
            raise ValueError(
                "USDA_API_KEY not found in environment. "
                "Please configure this key before using photo meal logging in production."
            )

    async def search_food(
        self, query: str, max_results: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Search USDA database for food item.
        
        Args:
            query: Food name to search for (e.g., "pizza", "hamburger")
            max_results: Number of results to return (default 1)
            
        Returns:
            Dict with nutrition info:
            {
                "name": "Pizza, cheese, regular crust",
                "fdc_id": 174987,
                "calories": 265,
                "protein_g": 11.0,
                "carbs_g": 33.0,
                "fat_g": 10.0,
                "serving_size": "100g",
                "confidence": "high"
            }
            
            Returns None if no match found.
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/foods/search",
                    params={
                        "api_key": self.api_key,
                        "query": query,
                        "pageSize": max_results,
                        "dataType": ["Survey (FNDDS)"],  # Most accurate for common foods
                    },
                )
                response.raise_for_status()
                
                data = response.json()
                if not data.get("foods"):
                    return None
                
                food = data["foods"][0]
                return self._extract_nutrition(food)
                
        except Exception as e:
            logger.warning(f"USDA API error for '{query}': {e}")
            return None

    def _extract_nutrition(self, food_data: dict) -> Dict[str, Any]:
        """Extract nutrition information from USDA food data.
        
        Args:
            food_data: Raw food data from USDA API
            
        Returns:
            Formatted nutrition dict
        """
        # Extract macronutrients from nutrients array
        nutrients = {n["nutrientName"]: n["value"] for n in food_data.get("foodNutrients", [])}
        
        return {
            "name": food_data.get("description", "Unknown food"),
            "fdc_id": food_data.get("fdcId"),
            "calories": nutrients.get("Energy", 0),
            "protein_g": nutrients.get("Protein", 0),
            "carbs_g": nutrients.get("Carbohydrate, by difference", 0),
            "fat_g": nutrients.get("Total lipid (fat)", 0),
            "serving_size": "100g",  # USDA data is per 100g
            "confidence": "high" if food_data.get("dataType") == "Survey (FNDDS)" else "medium",
        }

    async def lookup_by_fdc_id(self, fdc_id: int) -> Optional[Dict[str, Any]]:
        """Look up food by FDC ID (for mapped foods).
        
        Args:
            fdc_id: USDA FoodData Central ID
            
        Returns:
            Nutrition dict or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/food/{fdc_id}",
                    params={"api_key": self.api_key},
                )
                response.raise_for_status()
                
                food_data = response.json()
                return self._extract_nutrition(food_data)
                
        except Exception as e:
            logger.warning(f"USDA API error for FDC ID {fdc_id}: {e}")
            return None

    async def batch_search(self, queries: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Search for multiple foods in one batch.
        
        Args:
            queries: List of food names to search
            
        Returns:
            List of nutrition dicts (None for not found)
        """
        import asyncio
        
        tasks = [self.search_food(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to None
        return [r if not isinstance(r, Exception) else None for r in results]

    def get_food_mapping(self, vision_label: str) -> Optional[str]:
        """Map Vision API label to USDA search query.
        
        Args:
            vision_label: Label from Vision API (e.g., "burger")
            
        Returns:
            USDA search query (e.g., "hamburger") or None
        """
        # Load mapping from config (will implement in food_mapping.py)
        from .food_mapping import FOOD_MAPPING
        
        label_lower = vision_label.lower().strip()
        return FOOD_MAPPING.get(label_lower, label_lower)
