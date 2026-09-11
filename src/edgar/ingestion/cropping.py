from pathlib import Path

from PIL import Image

from edgar.domain import DocumentComponent, DocumentPage


class ComponentCropper:
    def __init__(self, *, storage_root: str | Path):
        self._storage_root = Path(storage_root)

    def crop(
        self,
        page: DocumentPage,
        component: DocumentComponent,
    ) -> DocumentComponent:
        self._validate_component_page_match(page, component)

        image_path = self._resolve_path(page.image_ref)

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

            crop_ref = self._crop_ref(page, component)
            crop_path = self._storage_root / crop_ref
            crop_path.parent.mkdir(parents=True, exist_ok=True)

            crop.save(crop_path, format="PNG")

        component.crop_ref = crop_ref.as_posix()

        return component

    def _resolve_path(self, image_ref: str) -> Path:
        path = Path(image_ref)

        if path.is_absolute():
            return path

        return self._storage_root / path

    def _crop_ref(
        self,
        page: DocumentPage,
        component: DocumentComponent,
    ) -> Path:
        return (
            Path("documents")
            / str(page.doc_id)
            / "crops"
            / f"page_{page.page_number:04d}"
            / f"{component.component_id}.png"
        )

    @staticmethod
    def _validate_component_page_match(
        page: DocumentPage,
        component: DocumentComponent,
    ) -> None:
        if component.doc_id != page.doc_id:
            raise ValueError("Component and page belong to different documents.")

        if component.page_index != page.page_index:
            raise ValueError("Component and page indexes do not match.")
