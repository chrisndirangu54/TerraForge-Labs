from __future__ import annotations

import re
from pathlib import Path


class PdfReportParser:
    """Extract text snippets and metadata from geological PDF reports."""

    def parse(self, filepath: str | Path) -> list[dict]:
        path = Path(filepath)
        content = path.read_bytes()
        text = self._extract_text(content)
        excerpt = " ".join(text.split())[:1200] if text else ""
        pages = self._page_count(content)
        keywords = self._keywords(text)

        return [
            {
                "sample_id": path.stem,
                "document_type": "pdf_report",
                "filename": path.name,
                "size_bytes": len(content),
                "page_count": pages,
                "text_excerpt": excerpt,
                "keywords": keywords,
                "lon": 37.5,
                "lat": -1.15,
                "flagged": not excerpt,
                "flag_reasons": [] if excerpt else ["no_extractable_text"],
            }
        ]

    def _extract_text(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader  # type: ignore[import-untyped]

            reader = PdfReader(__import__("io").BytesIO(content))
            chunks: list[str] = []
            for page in reader.pages[:12]:
                chunks.append(page.extract_text() or "")
            return "\n".join(chunks)
        except Exception:
            decoded = content.decode("latin-1", errors="ignore")
            strings = re.findall(r"\(([^()\\]{4,})\)", decoded)
            return " ".join(strings[:80])

    def _page_count(self, content: bytes) -> int:
        try:
            from pypdf import PdfReader  # type: ignore[import-untyped]

            return len(PdfReader(__import__("io").BytesIO(content)).pages)
        except Exception:
            return max(1, content.count(b"/Type /Page"))

    def _keywords(self, text: str) -> list[str]:
        terms = [
            "JORC",
            "assay",
            "drill",
            "lithology",
            "geochemistry",
            "resource",
            "reserve",
            "Ta",
            "Nb",
            "pegmatite",
        ]
        upper = text.upper()
        return [term for term in terms if term.upper() in upper][:8]