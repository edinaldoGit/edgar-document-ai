import pytest

from edgar.infrastructure.modal_layout_client import ModalLayoutClient


def test_rejects_blank_app_name():
    with pytest.raises(ValueError):
        ModalLayoutClient(app_name="   ")


def test_rejects_blank_class_name():
    with pytest.raises(ValueError):
        ModalLayoutClient(class_name="   ")


def test_rejects_empty_image():
    client = ModalLayoutClient()

    with pytest.raises(ValueError):
        client.analyze_image(b"")
