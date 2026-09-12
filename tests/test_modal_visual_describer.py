from uuid import uuid4

import pytest

from edgar.domain import (
    BoundingBox,
    ComponentType,
    DocumentComponent,
)
from edgar.infrastructure.modal_visual_describer import (
    ModalVisualDescriber,
)


class FakeVisualDescriptionClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def describe_image(
        self,
        image_bytes,
        *,
        prompt,
        context=None,
    ):
        self.calls.append(
            (
                image_bytes,
                prompt,
                context,
            )
        )

        return self.response


def make_component(*, crop_ref=None):
    return DocumentComponent(
        doc_id=uuid4(),
        page_index=0,
        component_type=ComponentType.FIGURE,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=100,
            y2=200,
        ),
        crop_ref=crop_ref,
    )


def test_describes_component_crop(tmp_path):
    crop_path = tmp_path / "figure.png"
    crop_path.write_bytes(b"fake-image")

    component = make_component(
        crop_ref="figure.png",
    )

    client = FakeVisualDescriptionClient(
        {
            "description": "Uma figura com três etapas.",
        }
    )

    describer = ModalVisualDescriber(
        client=client,
        storage_root=tmp_path,
    )

    result = describer.describe(
        component,
        prompt="Descreva a figura.",
        context="Figura 1 - Arquitetura.",
    )

    assert result == "Uma figura com três etapas."

    assert client.calls == [
        (
            b"fake-image",
            "Descreva a figura.",
            "Figura 1 - Arquitetura.",
        )
    ]


def test_returns_none_when_service_has_no_description(tmp_path):
    crop_path = tmp_path / "figure.png"
    crop_path.write_bytes(b"fake-image")

    component = make_component(
        crop_ref="figure.png",
    )

    client = FakeVisualDescriptionClient(
        {
            "description": None,
        }
    )

    describer = ModalVisualDescriber(
        client=client,
        storage_root=tmp_path,
    )

    assert (
        describer.describe(
            component,
            prompt="Descreva a figura.",
        )
        is None
    )


def test_rejects_component_without_crop(tmp_path):
    component = make_component()

    client = FakeVisualDescriptionClient(
        {
            "description": "texto",
        }
    )

    describer = ModalVisualDescriber(
        client=client,
        storage_root=tmp_path,
    )

    with pytest.raises(ValueError):
        describer.describe(
            component,
            prompt="Descreva a figura.",
        )


def test_rejects_missing_crop_file(tmp_path):
    component = make_component(
        crop_ref="missing.png",
    )

    client = FakeVisualDescriptionClient(
        {
            "description": "texto",
        }
    )

    describer = ModalVisualDescriber(
        client=client,
        storage_root=tmp_path,
    )

    with pytest.raises(FileNotFoundError):
        describer.describe(
            component,
            prompt="Descreva a figura.",
        )
