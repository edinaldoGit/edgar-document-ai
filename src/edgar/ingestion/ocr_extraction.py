import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from edgar.domain import Document, DocumentComponent, DocumentPage


class TesseractOCRTextExtractor:
    def __init__(
        self,
        *,
        storage_root: str | Path,
        languages: str = "por+eng",
        page_segmentation_mode: int = 6,
    ):
        if not languages.strip():
            raise ValueError("OCR languages must not be blank.")

        if page_segmentation_mode <= 0:
            raise ValueError("Page segmentation mode must be positive.")

        self._storage_root = Path(storage_root)
        self._languages = languages
        self._page_segmentation_mode = page_segmentation_mode

    def extract(
        self,
        document: Document,
        page: DocumentPage,
        component: DocumentComponent,
    ) -> str | None:
        self._validate_relationships(document, page, component)

        image_path = self._resolve_image_path(page.image_ref)

        if not image_path.is_file():
            raise FileNotFoundError(f"Page image not found: {image_path}")

        with Image.open(image_path) as image:
            if image.size != (page.width, page.height):
                raise RuntimeError("Page image dimensions do not match DocumentPage.")

            crop = image.crop(
                (
                    component.bbox.x1,
                    component.bbox.y1,
                    component.bbox.x2,
                    component.bbox.y2,
                )
            )

            with tempfile.NamedTemporaryFile(suffix=".png") as temporary_file:
                crop.save(temporary_file.name, format="PNG")

                process = subprocess.run(
                    [
                        "tesseract",
                        temporary_file.name,
                        "stdout",
                        "-l",
                        self._languages,
                        "--psm",
                        str(self._page_segmentation_mode),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

        if process.returncode != 0:
            raise RuntimeError(f"Tesseract OCR failed: {process.stderr.strip()}")

        text = process.stdout.strip()

        if not text:
            return None

        return text

    def _resolve_image_path(self, image_ref: str) -> Path:
        path = Path(image_ref)

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
