"""Text drawn inside a Form XObject must survive PDF extraction (pypdf layout mode skips it)."""

import io

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    FloatObject,
    NameObject,
)

from deploy_vii import preparation
from deploy_vii.preparation import APPENDED, PLAIN_ONLY, pdf_content
from deploy_workflow.model import handoff

WITH_FORM = b"BT /F1 12 Tf 72 700 Td (Page heading 2026) Tj ET q /Fm0 Do Q"
FORM_ONLY = b"q /Fm0 Do Q"
NO_FORM = b"BT /F1 12 Tf 72 700 Td (Page heading 2026) Tj ET"


def make(page_content: bytes = WITH_FORM) -> bytes:
    w = PdfWriter()
    page = w.add_blank_page(612, 792)
    font = w._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )
    fonts = DictionaryObject({NameObject("/F1"): font})
    form = DecodedStreamObject()
    form.set_data(b"BT /F1 12 Tf 72 600 Td (Revenue 4,275.5) Tj ET")
    form.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Form"),
            NameObject("/BBox"): ArrayObject([FloatObject(v) for v in (0, 0, 612, 792)]),
            NameObject("/Resources"): DictionaryObject({NameObject("/Font"): fonts}),
        }
    )
    content = DecodedStreamObject()
    content.set_data(page_content)
    page[NameObject("/Contents")] = w._add_object(content)
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): fonts,
            NameObject("/XObject"): DictionaryObject({NameObject("/Fm0"): w._add_object(form)}),
        }
    )
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()


@pytest.fixture
def no_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("OCR must not run when text was read")

    monkeypatch.setattr(preparation._Ocr, "page", refuse)


def test_a_form_text_appended_to_layout(no_ocr: None) -> None:
    result = pdf_content(make())
    assert [s.locator for s in result.spans] == ["page:1"]
    assert "Page heading 2026" in result.spans[0].text
    assert "Revenue 4,275.5" in result.spans[0].text
    cov = result.coverage[0]
    assert (cov.status, cov.limitation) == ("retained", APPENDED)


def test_b_form_only_page_read_in_reading_order(no_ocr: None) -> None:
    result = pdf_content(make(FORM_ONLY))
    assert "Revenue 4,275.5" in result.spans[0].text
    cov = result.coverage[0]
    assert (cov.status, cov.limitation) == ("retained", PLAIN_ONLY)


def test_c_page_without_form_is_byte_identical_to_layout(no_ocr: None) -> None:
    raw = make(NO_FORM)
    layout = (
        PdfReader(io.BytesIO(raw))
        .pages[0]
        .extract_text(extraction_mode="layout", layout_mode_strip_rotated=False)
    )
    result = pdf_content(raw)
    assert result.spans[0].text == layout
    assert result.coverage[0].limitation is None


def test_d_handoff_pages_keep_form_text() -> None:
    assert "Revenue 4,275.5" in handoff._pages("x.pdf", make())[0]
