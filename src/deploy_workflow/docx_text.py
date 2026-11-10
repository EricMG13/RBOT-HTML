"""A Word document's (.docx) text, for an issuer folder.

Body paragraphs in document order, each table row as its cells joined by `` | ``, tabs and line
breaks kept. Text a tracked change deleted (``w:delText``) is left out; headers, footers, footnotes
and comments are not read. Standard library only, through the workbook reader's guarded XML parse
(no DTD or entity declaration) and its expanded-size limit. Nothing in the file is run or followed.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from xml.etree.ElementTree import Element
from zipfile import ZipFile

from deploy_vii.preparation import MAX_EXPANDED_BYTES, xml_part

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_BREAKS = frozenset({f"{W}br", f"{W}cr"})
# Paragraph and run properties hold formatting, including <w:tab> tab stops, never text.
_PROPERTIES = frozenset({f"{W}pPr", f"{W}rPr"})


def docx_text(raw: bytes) -> str:
    """The text of the Word document ``raw``; raises on a file that is not one."""
    with ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len({info.filename for info in infos}) != len(infos):
            raise ValueError("duplicate ZIP members")
        if sum(info.file_size for info in infos) > MAX_EXPANDED_BYTES:
            raise ValueError("expanded document exceeds the extraction limit")
        body = xml_part(archive, "word/document.xml").find(f"{W}body")
    if body is None:
        raise ValueError("the document has no body")
    return "\n".join(_lines(body))


def _lines(parent: Element) -> Iterator[str]:
    for child in parent:
        if child.tag == f"{W}p":
            yield _paragraph(child)
        elif child.tag == f"{W}tbl":
            for row in child.findall(f"{W}tr"):
                cells = row.findall(f"{W}tc")
                yield " | ".join(" ".join(map(_paragraph, c.iter(f"{W}p"))) for c in cells)
        elif child.tag == f"{W}sdt" and (content := child.find(f"{W}sdtContent")) is not None:
            yield from _lines(content)


def _paragraph(paragraph: Element) -> str:
    parts: list[str] = []
    _collect(paragraph, parts)
    return "".join(parts)


def _collect(node: Element, parts: list[str]) -> None:
    for child in node:
        if child.tag == f"{W}t":
            parts.append(child.text or "")
        elif child.tag == f"{W}tab":
            parts.append("\t")
        elif child.tag in _BREAKS:
            parts.append("\n")
        elif child.tag not in _PROPERTIES:
            _collect(child, parts)
