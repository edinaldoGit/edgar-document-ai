from pathlib import Path
from typing import Any

from edgar.domain import DocumentComponent, DocumentPage
from edgar.ingestion.layout_geometry import detection_bbox_to_pixels
from edgar.ingestion.layout_labels import map_layout_label


class DocLayoutYOLOAnalyzer:
    def __init__(
        self,
        *,
        model: Any,
        storage_root: str | Path,
        image_size: int = 1024,
        confidence_threshold: float = 0.2,
        device: str = "cpu",
    ):
        if image_size <= 0:
            raise ValueError("Image size must be positive.")

        if not 0 <= confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1.")

        if not device.strip():
            raise ValueError("Device must not be blank.")

        self._model = model
        self._storage_root = Path(storage_root)
        self._image_size = image_size
        self._confidence_threshold = confidence_threshold
        self._device = device

    def analyze(self, page: DocumentPage) -> list[DocumentComponent]:
        image_path = self._resolve_image_path(page.image_ref)

        if not image_path.is_file():
            raise FileNotFoundError(f"Page image not found: {image_path}")

        results = self._model.predict(
            str(image_path),
            imgsz=self._image_size,
            conf=self._confidence_threshold,
            device=self._device,
        )

        if len(results) != 1:
            raise RuntimeError(f"Expected exactly one layout result, received {len(results)}.")

        result = results[0]
        components: list[DocumentComponent] = []

        for detection in result.boxes:
            class_id = int(detection.cls.item())
            confidence = float(detection.conf.item())
            coordinates = detection.xyxy[0].tolist()

            component = DocumentComponent(
                doc_id=page.doc_id,
                page_index=page.page_index,
                component_type=map_layout_label(result.names[class_id]),
                bbox=detection_bbox_to_pixels(
                    coordinates,
                    page_width=page.width,
                    page_height=page.height,
                ),
                detection_confidence=confidence,
            )

            components.append(component)

        return components

    def _resolve_image_path(self, image_ref: str) -> Path:
        path = Path(image_ref)

        if path.is_absolute():
            return path

        return self._storage_root / path
