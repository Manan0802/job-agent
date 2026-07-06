from markitdown import MarkItDown


def pdf_to_markdown(pdf_path: str) -> str:
    md = MarkItDown()
    result = md.convert(pdf_path)
    return result.text_content
