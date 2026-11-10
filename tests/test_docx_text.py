"""Word documents (.docx) in an issuer folder: their text, read without a Word library."""

import io
import zipfile

import pytest

from deploy_workflow.docx_text import docx_text

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def docx(body: str, *, extra: dict[str, str] | None = None) -> bytes:
    """A minimal Word file: ``body`` is the inside of ``<w:body>``."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "word/document.xml", f"<w:document {W}><w:body>{body}</w:body></w:document>"
        )
        for name, text in (extra or {}).items():
            archive.writestr(name, text)
    return out.getvalue()


def para(*runs: str) -> str:
    return "<w:p>" + "".join(f"<w:r>{r}</w:r>" for r in runs) + "</w:p>"


def test_paragraphs_runs_tabs_breaks_and_tables_in_document_order() -> None:
    table = (
        "<w:tbl>"
        "<w:tr><w:tc>"
        + para("<w:t>Facility</w:t>")
        + "</w:tc><w:tc>"
        + para("<w:t>USD m</w:t>")
        + "</w:tc></w:tr>"
        "<w:tr><w:tc>"
        + para("<w:t>Term loan B</w:t>")
        + "</w:tc><w:tc>"
        + para("<w:t>7,250</w:t>")
        + "</w:tc></w:tr>"
        "</w:tbl>"
    )
    body = (
        para("<w:t>Net sales were </w:t>", '<w:t xml:space="preserve">7,940.</w:t>')
        + table
        + para("<w:t>Margin</w:t>", "<w:tab/>", "<w:t>52%</w:t>", "<w:br/>", "<w:t>Next line</w:t>")
    )
    assert docx_text(docx(body)) == (
        "Net sales were 7,940.\nFacility | USD m\nTerm loan B | 7,250\nMargin\t52%\nNext line"
    )


def test_deleted_tracked_text_is_left_out_and_inserted_text_kept() -> None:
    body = para("<w:t>Leverage was </w:t>").replace(
        "</w:p>",
        "<w:del><w:r><w:delText>5.9x</w:delText></w:r></w:del>"
        "<w:ins><w:r><w:t>5.8x</w:t></w:r></w:ins></w:p>",
    )
    assert docx_text(docx(body)) == "Leverage was 5.8x"


def test_content_controls_are_read_through() -> None:
    body = (
        "<w:sdt><w:sdtContent>"
        + para("<w:t>Borrower: TransDigm Inc.</w:t>")
        + "</w:sdtContent></w:sdt>"
    )
    assert docx_text(docx(body)) == "Borrower: TransDigm Inc."


@pytest.mark.parametrize(
    "raw",
    [
        b"not a zip",
        docx("", extra={}).replace(b"word/document.xml", b"word/elsewhere.xml"),
        docx(para("<w:t>x</w:t>")).replace(b"<w:body>", b"<!DOCTYPE x><w:body>"),
    ],
    ids=["not-a-zip", "no-document-part", "dtd"],
)
def test_a_file_that_is_not_a_plain_word_document_raises(raw: bytes) -> None:
    with pytest.raises((ValueError, KeyError, zipfile.BadZipFile)):
        docx_text(raw)


def test_tab_stops_in_paragraph_properties_are_not_text() -> None:
    body = (
        '<w:p><w:pPr><w:tabs><w:tab w:val="left" w:pos="720"/></w:tabs></w:pPr>'
        "<w:r><w:rPr><w:b/></w:rPr><w:t>Cash</w:t></w:r><w:r><w:tab/><w:t>1,200</w:t></w:r></w:p>"
    )
    assert docx_text(docx(body)) == "Cash\t1,200"
