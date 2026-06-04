import pytest
from pathlib import Path
from converter.converters.image_converter import ImageConverter


@pytest.fixture
def converter():
    return ImageConverter()


def test_png_to_pdf(converter, sample_dir, tmp_path):
    out = tmp_path / "out.pdf"
    result = converter.convert(sample_dir / "sample.png", out)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0
    assert out.read_bytes()[:4] == b"%PDF"


def test_jpg_to_pdf(converter, sample_dir, tmp_path):
    out = tmp_path / "out.pdf"
    result = converter.convert(sample_dir / "sample.jpg", out)
    assert out.read_bytes()[:4] == b"%PDF"


def test_bmp_to_pdf(converter, sample_dir, tmp_path):
    out = tmp_path / "out.pdf"
    converter.convert(sample_dir / "sample.bmp", out)
    assert out.read_bytes()[:4] == b"%PDF"


def test_gif_to_pdf(converter, sample_dir, tmp_path):
    out = tmp_path / "out.pdf"
    converter.convert(sample_dir / "sample.gif", out)
    assert out.read_bytes()[:4] == b"%PDF"


def test_supports_extensions(converter):
    for ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"]:
        assert converter.supports(ext)
    assert not converter.supports(".docx")


def test_missing_file_raises(converter, tmp_path):
    from converter.exceptions import ConversionError
    with pytest.raises(ConversionError):
        converter.convert(tmp_path / "nonexistent.png", tmp_path / "out.pdf")
