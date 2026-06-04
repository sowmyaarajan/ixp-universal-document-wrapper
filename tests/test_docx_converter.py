import pytest
from converter.converters.docx_converter import DocxConverter
from converter.converters.ms_office_converter import is_ms_office_available

word_available = is_ms_office_available("Word.Application")


@pytest.mark.skipif(not word_available, reason="MS Word not installed")
def test_docx_via_ms_office(sample_dir, tmp_path):
    out = tmp_path / "out.pdf"
    converter = DocxConverter()
    result = converter.convert(sample_dir / "sample.docx", out)
    assert result.read_bytes()[:4] == b"%PDF"


def test_supports_extensions():
    for ext in [".docx", ".doc"]:
        assert DocxConverter.supports(ext)
    assert not DocxConverter.supports(".xlsx")
