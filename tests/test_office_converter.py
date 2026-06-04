import pytest
from converter.converters.ms_office_converter import MSOfficeConverter, is_ms_office_available

word_available = is_ms_office_available("Word.Application")
excel_available = is_ms_office_available("Excel.Application")
ppt_available = is_ms_office_available("PowerPoint.Application")

skip_no_word = pytest.mark.skipif(not word_available, reason="MS Word not installed")
skip_no_excel = pytest.mark.skipif(not excel_available, reason="MS Excel not installed")
skip_no_ppt = pytest.mark.skipif(not ppt_available, reason="MS PowerPoint not installed")


@skip_no_word
def test_docx_to_pdf(sample_dir, tmp_path):
    out = tmp_path / "out.pdf"
    result = MSOfficeConverter().convert(sample_dir / "sample.docx", out)
    assert result.read_bytes()[:4] == b"%PDF"


@skip_no_excel
def test_xlsx_to_pdf(sample_dir, tmp_path):
    out = tmp_path / "out.pdf"
    result = MSOfficeConverter().convert(sample_dir / "sample.xlsx", out)
    assert result.read_bytes()[:4] == b"%PDF"


@skip_no_ppt
def test_pptx_to_pdf(sample_dir, tmp_path):
    out = tmp_path / "out.pdf"
    result = MSOfficeConverter().convert(sample_dir / "sample.pptx", out)
    assert result.read_bytes()[:4] == b"%PDF"


def test_supports_extensions():
    for ext in [".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"]:
        assert MSOfficeConverter.supports(ext)
    assert not MSOfficeConverter.supports(".png")
