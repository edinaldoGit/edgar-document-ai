from pathlib import Path

import pymupdf

from edgar.domain import Document, DocumentComponent, DocumentPage
from edgar.ingestion.pdf_geometry import bbox_pixels_to_page_points


class PyMuPDFTextExtractor:
    def __init__(self, *, storage_root: str | Path):
        self._storage_root = Path(storage_root)

    def extract(
        self,
        document: Document,
        page: DocumentPage,
        component: DocumentComponent,
    ) -> str | None:
        self._validate_relationships(document, page, component)

        source_path = self._resolve_source_path(document.source_ref)

        if not source_path.is_file():
            raise FileNotFoundError(f"PDF source not found: {source_path}")

        with pymupdf.open(source_path) as pdf:
            if page.page_index >= len(pdf):
                raise RuntimeError("DocumentPage index does not exist in the PDF source.")

            pdf_page = pdf[page.page_index]

            x1, y1, x2, y2 = bbox_pixels_to_page_points(
                component.bbox,
                pixel_width=page.width,
                pixel_height=page.height,
                page_width_points=pdf_page.rect.width,
                page_height_points=pdf_page.rect.height,
            )

            clip = pymupdf.Rect(x1, y1, x2, y2)

            text = pdf_page.get_text(
                "text",
                clip=clip,
            ).strip()

        if not text:
            return None

        return text

    def _resolve_source_path(self, source_ref: str) -> Path:
        path = Path(source_ref)

        if path.is_absolute():
            return path

        return self._storage_root / path

    @staticmethod
    def _validate_relationships(
        document: Document,
        page: DocumentPage,
        component: DocumentComponent,
    ) -> None:
        if page.doc_id != document.doc_id:
            raise ValueError("Page does not belong to the document.")

        if component.doc_id != document.doc_id:
            raise ValueError("Component does not belong to the document.")

        if component.page_index != page.page_index:
            raise ValueError("Component and page indexes do not match.")
