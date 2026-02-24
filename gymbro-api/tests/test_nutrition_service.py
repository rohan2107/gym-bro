"""Tests for Nutrition service (USDA FoodData Central API integration)."""

from typing import Any

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.nutrition import NutritionService


@pytest.fixture
def nutrition_service() -> NutritionService:
    """Create NutritionService instance for testing.
    
    Mock mode is disabled to allow HTTP mocking in tests.
    """
    return NutritionService(mock_mode=False)


@pytest.fixture
def mock_usda_response() -> dict[str, Any]:
    """Mock USDA API response."""
    return {
        "foods": [
            {
                "fdcId": 174987,
                "description": "Pizza, cheese, regular crust",
                "dataType": "Survey (FNDDS)",
                "foodNutrients": [
                    {"nutrientName": "Energy", "value": 265},
                    {"nutrientName": "Protein", "value": 11.0},
                    {"nutrientName": "Carbohydrate, by difference", "value": 33.0},
                    {"nutrientName": "Total lipid (fat)", "value": 10.0},
                ]
            }
        ]
    }


@pytest.fixture
def mock_food_detail_response() -> dict[str, Any]:
    """Mock USDA API food detail response."""
    return {
        "fdcId": 174987,
        "description": "Pizza, cheese, regular crust",
        "dataType": "Survey (FNDDS)",
        "foodNutrients": [
            {"nutrientName": "Energy", "value": 265},
            {"nutrientName": "Protein", "value": 11.0},
            {"nutrientName": "Carbohydrate, by difference", "value": 33.0},
            {"nutrientName": "Total lipid (fat)", "value": 10.0},
        ]
    }


class TestNutritionService:
    """Test suite for NutritionService."""

    def test_initialization(self, nutrition_service: NutritionService) -> None:
        """Test NutritionService initializes correctly."""
        assert nutrition_service is not None
        # Tests explicitly set mock_mode=False to allow HTTP mocking
        assert nutrition_service.mock_mode is False
        assert nutrition_service.BASE_URL == "https://api.nal.usda.gov/fdc/v1"

    @pytest.mark.asyncio
    async def test_search_food_success(self, nutrition_service: NutritionService, mock_usda_response: dict[str, Any]) -> None:
        """Test successful food search."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_usda_response
            mock_response.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            # Test search
            result = await nutrition_service.search_food("pizza")
            
            assert result is not None
            assert result["name"] == "Pizza, cheese, regular crust"
            assert result["fdc_id"] == 174987
            assert result["calories"] == 265
            assert result["protein_g"] == 11.0
            assert result["carbs_g"] == 33.0
            assert result["fat_g"] == 10.0
            assert result["serving_size"] == "100g"
            assert result["confidence"] == "high"

    @pytest.mark.asyncio
    async def test_search_food_no_results(self, nutrition_service: NutritionService) -> None:
        """Test food search with no results."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock with empty results
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"foods": []}
            mock_response.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            # Test search
            result = await nutrition_service.search_food("nonexistentfood123")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_search_food_api_error(self, nutrition_service: NutritionService) -> None:
        """Test food search handles API errors gracefully."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock to raise error
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("API Error")
            )
            
            # Test search - should return None on error
            result = await nutrition_service.search_food("pizza")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_lookup_by_fdc_id_success(self, nutrition_service: NutritionService, mock_food_detail_response: dict[str, Any]) -> None:
        """Test successful FDC ID lookup."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_food_detail_response
            mock_response.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            # Test lookup
            result = await nutrition_service.lookup_by_fdc_id(174987)
            
            assert result is not None
            assert result["fdc_id"] == 174987
            assert result["name"] == "Pizza, cheese, regular crust"

    @pytest.mark.asyncio
    async def test_lookup_by_fdc_id_not_found(self, nutrition_service: NutritionService) -> None:
        """Test FDC ID lookup when not found."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock to raise HTTP error
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Not found")
            )
            
            # Test lookup
            result = await nutrition_service.lookup_by_fdc_id(999999)
            
            assert result is None

    @pytest.mark.asyncio
    async def test_batch_search_multiple_foods(self, nutrition_service: NutritionService, mock_usda_response: dict[str, Any]) -> None:
        """Test batch search for multiple foods."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_usda_response
            mock_response.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            # Test batch search
            queries = ["pizza", "burger", "salad"]
            results = await nutrition_service.batch_search(queries)
            
            assert len(results) == 3
            # All results should be dicts or None
            for result in results:
                assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_batch_search_handles_errors(self, nutrition_service: NutritionService) -> None:
        """Test batch search handles individual errors gracefully."""
        with patch('httpx.AsyncClient') as mock_client:
            # First call succeeds, second fails, third succeeds
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"foods": []}
            mock_response_success.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[mock_response_success, Exception("Error"), mock_response_success]
            )
            
            # Test batch search
            results = await nutrition_service.batch_search(["food1", "food2", "food3"])
            
            assert len(results) == 3
            # Second result should be None due to error
            assert results[1] is None

    def test_extract_nutrition_complete_data(self, nutrition_service: NutritionService) -> None:
        """Test nutrition extraction with complete data."""
        food_data: dict[str, Any] = {
            "fdcId": 12345,
            "description": "Test Food",
            "dataType": "Survey (FNDDS)",
            "foodNutrients": [
                {"nutrientName": "Energy", "value": 200},
                {"nutrientName": "Protein", "value": 15},
                {"nutrientName": "Carbohydrate, by difference", "value": 25},
                {"nutrientName": "Total lipid (fat)", "value": 8},
            ]
        }
        
        result = nutrition_service._extract_nutrition(food_data)  # pyright: ignore[reportPrivateUsage]
        
        assert result["name"] == "Test Food"
        assert result["fdc_id"] == 12345
        assert result["calories"] == 200
        assert result["protein_g"] == 15
        assert result["carbs_g"] == 25
        assert result["fat_g"] == 8
        assert result["confidence"] == "high"

    def test_extract_nutrition_missing_nutrients(self, nutrition_service: NutritionService) -> None:
        """Test nutrition extraction with missing nutrient data."""
        food_data: dict[str, Any] = {
            "fdcId": 12345,
            "description": "Incomplete Food",
            "dataType": "Branded",
            "foodNutrients": []
        }
        
        result = nutrition_service._extract_nutrition(food_data)  # pyright: ignore[reportPrivateUsage]
        
        assert result["name"] == "Incomplete Food"
        assert result["calories"] == 0
        assert result["protein_g"] == 0
        assert result["carbs_g"] == 0
        assert result["fat_g"] == 0
        assert result["confidence"] == "medium"  # Not FNDDS data

    def test_get_food_mapping(self, nutrition_service: NutritionService) -> None:
        """Test food mapping loads correctly."""
        # Test a mapped food
        result = nutrition_service.get_food_mapping("burger")
        assert result == "hamburger, plain"
        
        # Test an unmapped food (returns itself)
        result = nutrition_service.get_food_mapping("unknownfood")
        assert result == "unknownfood"

    @pytest.mark.asyncio
    async def test_search_food_with_max_results(self, nutrition_service: NutritionService, mock_usda_response: dict[str, Any]) -> None:
        """Test search_food respects max_results parameter."""
        with patch('httpx.AsyncClient') as mock_client:
            # Setup mock
            mock_response = MagicMock()
            mock_response.status_code = 200
            # Return multiple foods
            multi_food_response: dict[str, Any] = {
                "foods": [
                    mock_usda_response["foods"][0],
                    {
                        "fdcId": 999,
                        "description": "Another food",
                        "dataType": "Branded",
                        "foodNutrients": []
                    }
                ]
            }
            mock_response.json.return_value = multi_food_response
            mock_response.raise_for_status = MagicMock()
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            # Test with max_results=1 (default) - should return first food
            result = await nutrition_service.search_food("pizza", max_results=1)
            
            assert result is not None
            assert result["fdc_id"] == 174987  # First food
