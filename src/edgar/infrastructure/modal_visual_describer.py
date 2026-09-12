from pathlib import Path

from edgar.domain import DocumentComponent
from edgar.infrastructure.modal_visual_description_client import (
    ModalVisualDescriptionClient,
)


class ModalVisualDescriber:
    def __init__(
        self,
        *,
        client: ModalVisualDescriptionClient,
        storage_root: str | Path,
    ):
        self._client = client
        self._storage_root = Path(storage_root)

    def describe(
        self,
        component: DocumentComponent,
        *,
        prompt: str,
        context: str | None = None,
    ) -> str | None:
        if component.crop_ref is None:
            raise ValueError("Component must have a visual crop before description.")

        image_path = self._resolve_crop_path(
            component.crop_ref,
        )

        if not image_path.is_file():
            raise FileNotFoundError(f"Component crop not found: {image_path}")

        response = self._client.describe_image(
            image_path.read_bytes(),
            prompt=prompt,
            context=context,
        )

        description = response.get("description")

        if description is None:
            return None

        if not isinstance(description, str):
            raise RuntimeError("Modal visual description service returned an invalid description.")

        description = description.strip()

        if not description:
            return None

        return description

    def _resolve_crop_path(self, crop_ref: str) -> Path:
        path = Path(crop_ref)

        if path.is_absolute():
            return path

        return self._storage_root / path
