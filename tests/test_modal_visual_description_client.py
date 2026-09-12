import pytest

from edgar.infrastructure.modal_visual_description_client import (
    ModalVisualDescriptionClient,
)


def test_rejects_blank_app_name():
    with pytest.raises(ValueError):
        ModalVisualDescriptionClient(
            app_name="   ",
        )


def test_rejects_blank_class_name():
    with pytest.raises(ValueError):
        ModalVisualDescriptionClient(
            class_name="   ",
        )


def test_rejects_empty_image():
    client = ModalVisualDescriptionClient()

    with pytest.raises(ValueError):
        client.describe_image(
            b"",
            prompt="Describe the image.",
        )


def test_rejects_blank_prompt():
    client = ModalVisualDescriptionClient()

    with pytest.raises(ValueError):
        client.describe_image(
            b"image",
            prompt="   ",
        )
