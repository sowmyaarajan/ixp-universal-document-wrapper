import pytest
from pathlib import Path
from converter import DocumentConverter, UnsupportedFormatError


@pytest.fixture
def dc():
    return DocumentConverter()


def test_check_dependencies():
    deps = DocumentConverter.check_dependencies()
    assert "pillow" in deps
    assert "pywin32" in deps
    assert "ms_office_word" in deps
    assert "ms_office_excel" in deps
    assert "ms_office_powerpoint" in deps
    assert isinstance(deps["pillow"], bool)


def test_supported_extensions(dc):
    exts = dc.get_supported_extensions()
    for ext in [".png", ".jpg", ".docx", ".xlsx", ".pptx"]:
        assert ext in exts


def test_unsupported_format_raises(dc, tmp_path):
    f = tmp_path / "file.xyz"
    f.write_bytes(b"dummy")
    with pytest.raises(UnsupportedFormatError):
        dc.convert_to_pdf(f, tmp_path / "out.pdf")


def test_pdf_passthrough(dc, tmp_path):
    src = tmp_path / "input.pdf"
    src.write_bytes(b"%PDF-1.4 fake pdf content")
    out = tmp_path / "output.pdf"
    result = dc.convert_to_pdf(src, out)
    assert result == out
    assert out.read_bytes() == src.read_bytes()


def test_is_already_pdf(dc, tmp_path):
    pdf = tmp_path / "real.pdf"
    pdf.write_bytes(b"%PDF-1.5 content")
    assert dc.is_already_pdf(pdf) is True

    not_pdf = tmp_path / "fake.txt"
    not_pdf.write_bytes(b"hello world")
    assert dc.is_already_pdf(not_pdf) is False


def test_image_via_document_converter(dc, sample_dir, tmp_path):
    out = tmp_path / "from_png.pdf"
    result = dc.convert_to_pdf(sample_dir / "sample.png", out)
    assert result.read_bytes()[:4] == b"%PDF"


def test_auto_output_path(dc, sample_dir):
    result = dc.convert_to_pdf(sample_dir / "sample.jpg")
    assert result == (sample_dir / "sample.pdf").resolve()
    assert result.exists()
    result.unlink()
