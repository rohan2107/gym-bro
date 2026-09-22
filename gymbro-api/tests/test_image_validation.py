"""Tests for the local image checks shared by every recognition provider."""

from io import BytesIO

import pytest
from PIL import Image

from app.services.image_validation import validate_image


@pytest.fixture
def valid_image_bytes():
    buffer = BytesIO()
    Image.new("RGB", (400, 400), color="red").save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def small_image_bytes():
    buffer = BytesIO()
    Image.new("RGB", (100, 100), color="blue").save(buffer, format="JPEG")
    return buffer.getvalue()


class TestValidateImage:
    """Image validation runs locally, before any API call."""

    def test_validate_image_valid(self, valid_image_bytes):
        """Test image validation passes for valid image."""
        result = validate_image(valid_image_bytes)

        assert result["valid"] is True
        assert "format" in result
        assert "size_kb" in result
        assert "dimensions" in result
        assert result["format"] in ["jpeg", "jpg", "png"]

    def test_validate_image_too_small(self, small_image_bytes):
        """Test image validation rejects images that are too small."""
        result = validate_image(small_image_bytes)

        assert result["valid"] is False
        assert "too small" in result["error"].lower()

    def test_validate_image_too_large(self):
        """Test image validation rejects images over 10MB."""
        # Create 11MB of data
        large_data = b"x" * (11 * 1024 * 1024)

        result = validate_image(large_data)

        # Will fail on Image.open since it's not a valid image,
        # but that's expected for invalid data
        assert result["valid"] is False

    def test_validate_image_invalid_data(self):
        """Test image validation rejects invalid image data."""
        invalid_data = b"not an image"

        result = validate_image(invalid_data)

        assert result["valid"] is False
        assert "error" in result
        assert "invalid" in result["error"].lower()

    def test_validate_image_png_format(self):
        """Test image validation accepts PNG format."""
        image = Image.new('RGB', (300, 300), color='purple')
        buffer = BytesIO()
        image.save(buffer, format='PNG')

        result = validate_image(buffer.getvalue())

        assert result["valid"] is True
        assert result["format"] == "png"

    def test_validate_image_webp_format(self):
        """Test image validation accepts WebP format."""
        image = Image.new('RGB', (300, 300), color='yellow')
        buffer = BytesIO()
        image.save(buffer, format='WEBP')

        result = validate_image(buffer.getvalue())

        assert result["valid"] is True
        assert result["format"] == "webp"

    @pytest.mark.parametrize("brand", [b"heic", b"heix", b"mif1", b"hevc"])
    def test_validate_image_rejects_heic_with_actionable_message(self, brand):
        """iPhone/macOS HEIC photos get a clear message, not Pillow's error."""
        heic = b"\x00\x00\x00\x18ftyp" + brand + b"\x00" * 300

        result = validate_image(heic)

        assert result["valid"] is False
        assert "HEIC" in result["error"]
        assert "JPEG" in result["error"]

    def test_validate_image_error_does_not_leak_internals(self):
        """Pillow's exception text includes object reprs and must not reach users."""
        result = validate_image(b"definitely not an image")

        assert result["valid"] is False
        assert "BytesIO" not in result["error"]
        assert "0x" not in result["error"]
        assert "JPEG" in result["error"]

    def test_validate_image_accepts_mpo_as_its_first_frame(self):
        """macOS Continuity Camera and some Photos exports produce MPO: a real JPEG photo
        followed by an extra frame (depth or thumbnail) appended after it. Confirmed live
        against Gemini on 2026-09-22 that the extra frame is silently ignored downstream."""
        first_frame = Image.new("RGB", (400, 400), color="green")
        second_frame = Image.new("RGB", (400, 400), color="black")
        buffer = BytesIO()
        first_frame.save(buffer, format="MPO", save_all=True, append_images=[second_frame])
        assert Image.open(BytesIO(buffer.getvalue())).format == "MPO"  # the fixture is real MPO

        result = validate_image(buffer.getvalue())

        assert result["valid"] is True
        assert result["format"] == "jpeg"
        assert result["dimensions"] == "400x400"

    def test_validate_image_mpo_still_enforces_the_minimum_dimensions(self):
        first_frame = Image.new("RGB", (100, 100), color="green")
        second_frame = Image.new("RGB", (100, 100), color="black")
        buffer = BytesIO()
        first_frame.save(buffer, format="MPO", save_all=True, append_images=[second_frame])

        result = validate_image(buffer.getvalue())

        assert result["valid"] is False
        assert "too small" in result["error"].lower()
