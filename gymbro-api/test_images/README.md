# Test Images for Vision API Development

This directory contains test images for validating the Google Cloud Vision API
food detection in Phase 4 development.

## Image Requirements

- **Format**: JPEG, PNG, or WebP
- **Size**: Between 200x200px and 4096x4096px
- **File size**: Under 10MB
- **Content**: Clear, well-lit photos of food

## Recommended Test Images

Add the following types of images to this directory for comprehensive testing:

### 1. Common Foods (High Confidence Expected)
- `pizza.jpg` - Cheese pizza slice or whole pizza
- `burger.jpg` - Hamburger or cheeseburger
- `salad.jpg` - Green salad with vegetables
- `chicken.jpg` - Grilled chicken breast
- `pasta.jpg` - Pasta with sauce

### 2. Beverages
- `coffee.jpg` - Cup of coffee or latte
- `smoothie.jpg` - Fruit smoothie

### 3. Breakfast Items
- `eggs.jpg` - Scrambled or fried eggs
- `pancakes.jpg` - Stack of pancakes
- `toast.jpg` - Toast with toppings

### 4. Edge Cases
- `multiple-items.jpg` - Plate with multiple distinct foods
- `blurry.jpg` - Intentionally blurry food photo
- `dark.jpg` - Poorly lit food photo
- `non-food.jpg` - Non-food item (e.g., laptop, book)

## Usage

These images will be used to:

1. **Manual testing** - Upload via API during development
2. **Automated tests** - Integration tests for Vision API service
3. **Confidence validation** - Verify >70% confidence threshold
4. **Edge case handling** - Test error handling and fallbacks

## Getting Images

You can:
- Take your own photos with your phone
- Use free stock photos from [Unsplash](https://unsplash.com/s/photos/food) or [Pexels](https://www.pexels.com/search/food/)
- Generate with AI tools (DALL-E, Midjourney)

## Notes

- Images are NOT committed to git (see .gitignore)
- Keep test images under 2MB for faster uploads
- Use diverse food types to test Vision API accuracy
- Add new images as you discover problematic food categories
