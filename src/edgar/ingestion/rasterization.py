from pathlib import Path

import pymupdf

from edgar.domain import Document, DocumentPage


class PyMuPDFRasterizer:
    def __init__(
        self,
        *,
        storage_root: str | Path,
        dpi: int = 300,
    ) -> None:
        if dpi <= 0:
            raise ValueError("DPI must be greater than zero.")

        self._storage_root = Path(storage_root)
        self._dpi = dpi

    @property
    def dpi(self) -> int:
        return self._dpi

    def rasterize(self, document: Document) -> list[DocumentPage]:
        source_path = self._resolve_source_path(document.source_ref)

        if not source_path.is_file():
            raise FileNotFoundError(f"PDF file not found: {source_path}")

        output_dir = self._storage_root / "documents" / str(document.doc_id) / "pages"
        output_dir.mkdir(parents=True, exist_ok=True)

        pages: list[DocumentPage] = []

        with pymupdf.open(str(source_path)) as pdf:
            if pdf.page_count != document.page_count:
                raise ValueError("Document page count does not match the source PDF.")

            for page_index, pdf_page in enumerate(pdf):
                pixmap = pdf_page.get_pixmap(
                    dpi=self._dpi,
                    alpha=False,
                )

                filename = f"page_{page_index + 1:04d}.png"
                output_path = output_dir / filename

                pixmap.save(str(output_path))

                image_ref = output_path.relative_to(self._storage_root).as_posix()

                pages.append(
                    DocumentPage(
                        doc_id=document.doc_id,
                        page_index=page_index,
                        width=pixmap.width,
                        height=pixmap.height,
                        render_dpi=self._dpi,
                        image_ref=image_ref,
                    )
                )

        return pages

    def _resolve_source_path(self, source_ref: str) -> Path:
        source_path = Path(source_ref)

        if source_path.is_absolute():
            return source_path

        return self._storage_root / source_path
