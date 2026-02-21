"""Food label to USDA search query mapping.

This module maps Vision API labels to USDA FoodData Central search queries.
The mapping helps improve accuracy by handling synonyms, regional variations,
and common food names.

Update this mapping as you discover better USDA matches during testing.
"""

# Vision API label -> USDA search query
FOOD_MAPPING = {
    # Pizza varieties
    "pizza": "pizza, cheese, regular crust",
    "pizza slice": "pizza, cheese, regular crust",
    
    # Burgers and sandwiches
    "burger": "hamburger, plain",
    "hamburger": "hamburger, plain",
    "cheeseburger": "cheeseburger, plain",
    "sandwich": "sandwich, chicken",
    
    # Chicken
    "chicken": "chicken breast, grilled",
    "fried chicken": "chicken, fried",
    "chicken breast": "chicken breast, grilled",
    "chicken wings": "chicken wings, fried",
    
    # Beef
    "steak": "beef steak, grilled",
    "beef": "beef, ground, cooked",
    
    # Pasta
    "pasta": "pasta, cooked",
    "spaghetti": "spaghetti with tomato sauce",
    "mac and cheese": "macaroni and cheese",
    "macaroni": "macaroni and cheese",
    
    # Rice and grains
    "rice": "rice, white, cooked",
    "fried rice": "fried rice",
    "brown rice": "rice, brown, cooked",
    
    # Vegetables
    "salad": "salad, green, with dressing",
    "french fries": "french fries",
    "fries": "french fries",
    "broccoli": "broccoli, cooked",
    "carrots": "carrots, raw",
    
    # Breakfast
    "eggs": "egg, whole, cooked",
    "scrambled eggs": "egg, scrambled",
    "bacon": "bacon, cooked",
    "pancakes": "pancake",
    "waffle": "waffle, plain",
    "toast": "bread, white, toasted",
    "cereal": "cereal, ready-to-eat",
    "oatmeal": "oatmeal, cooked",
    
    # Desserts
    "cake": "cake, chocolate",
    "cookie": "cookies, chocolate chip",
    "cookies": "cookies, chocolate chip",
    "ice cream": "ice cream, vanilla",
    "brownie": "brownie",
    
    # Snacks
    "chips": "potato chips",
    "popcorn": "popcorn, plain",
    "nuts": "mixed nuts",
    "pretzels": "pretzels",
    
    # Drinks (approximate calories - mainly for coffee/smoothies)
    "coffee": "coffee, black",
    "latte": "coffee, latte",
    "smoothie": "smoothie, fruit",
    "juice": "orange juice",
    "soda": "soda, cola",
    
    # Fast food
    "taco": "taco, beef",
    "burrito": "burrito, bean and cheese",
    "nachos": "nachos with cheese",
    "hot dog": "hot dog with bun",
    "sub": "submarine sandwich",
    "wrap": "wrap, chicken",
    
    # Asian food
    "sushi": "sushi roll",
    "ramen": "ramen noodles",
    "dumplings": "dumplings, steamed",
    "spring roll": "spring roll",
    "pad thai": "pad thai",
    
    # Mexican food
    "quesadilla": "quesadilla, cheese",
    "enchilada": "enchilada, beef",
    "fajitas": "fajitas, chicken",
    
    # Seafood
    "salmon": "salmon, cooked",
    "fish": "fish fillet, baked",
    "shrimp": "shrimp, cooked",
    "tuna": "tuna, canned in water",
}

# FDC IDs for common foods (optional - for faster lookup)
# You can populate this as you discover good matches
FDC_ID_MAPPING = {
    # Format: "food_name": fdc_id
    # Example: "pizza": 174987,
    # Add these during testing to speed up lookups
}


def get_search_query(vision_label: str) -> str:
    """Get USDA search query for a vision label.
    
    Args:
        vision_label: Label from Vision API
        
    Returns:
        USDA search query string
    """
    label_lower = vision_label.lower().strip()
    return FOOD_MAPPING.get(label_lower, label_lower)


def get_fdc_id(vision_label: str) -> int:
    """Get FDC ID for a vision label if mapped.
    
    Args:
        vision_label: Label from Vision API
        
    Returns:
        FDC ID or None
    """
    label_lower = vision_label.lower().strip()
    return FDC_ID_MAPPING.get(label_lower)
