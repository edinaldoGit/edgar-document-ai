from pathlib import Path

from edgar.domain import DocumentComponent, DocumentPage
from edgar.infrastructure.modal_layout_client import ModalLayoutClient
from edgar.ingestion.layout_geometry import detection_bbox_to_pixels
from edgar.ingestion.layout_labels import map_layout_label


class ModalLayoutAnalyzer:
    def __init__(
        self,
        *,
        client: ModalLayoutClient,
        storage_root: str | Path,
    ):
        self._client = client
        self._storage_root = Path(storage_root)

    def analyze(self, page: DocumentPage) -> list[DocumentComponent]:
        image_path = self._resolve_image_path(page.image_ref)

        if not image_path.is_file():
            raise FileNotFoundError(f"Page image not found: {image_path}")

        image_bytes = image_path.read_bytes()
        response = self._client.analyze_image(image_bytes)

        original_shape = response.get("original_shape")

        if original_shape is None or len(original_shape) != 2:
            raise RuntimeError("Modal layout service returned an invalid original shape.")

        remote_height, remote_width = original_shape

        if remote_width != page.width or remote_height != page.height:
            raise RuntimeError("Modal layout service image dimensions do not match DocumentPage.")

        detections = response.get("detections")

        if not isinstance(detections, list):
            raise RuntimeError("Modal layout service returned invalid detections.")

        components: list[DocumentComponent] = []

        for detection in detections:
            component = DocumentComponent(
                doc_id=page.doc_id,
                page_index=page.page_index,
                component_type=map_layout_label(detection["class_name"]),
                bbox=detection_bbox_to_pixels(
                    detection["xyxy"],
                    page_width=page.width,
                    page_height=page.height,
                ),
                detection_confidence=float(detection["confidence"]),
            )

            components.append(component)

        return components

    def _resolve_image_path(self, image_ref: str) -> Path:
        path = Path(image_ref)

        if path.is_absolute():
            return path

        return self._storage_root / path
