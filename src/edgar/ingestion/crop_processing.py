from edgar.domain import DocumentComponent, DocumentPage
from edgar.ingestion.cropping import ComponentCropper
from edgar.ingestion.cropping_policy import requires_visual_crop


class VisualCropProcessor:
    def __init__(self, *, cropper: ComponentCropper):
        self._cropper = cropper

    def process(
        self,
        page: DocumentPage,
        components: list[DocumentComponent],
    ) -> list[DocumentComponent]:
        for component in components:
            if requires_visual_crop(component):
                self._cropper.crop(page, component)

        return components
