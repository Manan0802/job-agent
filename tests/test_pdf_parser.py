from unittest.mock import patch, MagicMock
from backend.utils import pdf_parser


def test_pdf_to_markdown_returns_text():
    fake_result = MagicMock(text_content="# Manan\nSoftware Engineer")
    with patch.object(pdf_parser, "MarkItDown") as MD:
        MD.return_value.convert.return_value = fake_result
        out = pdf_parser.pdf_to_markdown("dummy.pdf")
    assert "Software Engineer" in out
