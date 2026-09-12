import pytest

from edgar.infrastructure.modal_embedding_client import (
    ModalEmbeddingClient,
)


def test_rejects_blank_app_name():
    with pytest.raises(ValueError):
        ModalEmbeddingClient(
            app_name="   ",
        )


def test_rejects_blank_class_name():
    with pytest.raises(ValueError):
        ModalEmbeddingClient(
            class_name="   ",
        )


def test_rejects_empty_texts():
    client = ModalEmbeddingClient()

    with pytest.raises(ValueError):
        client.embed_texts([])


def test_rejects_blank_text():
    client = ModalEmbeddingClient()

    with pytest.raises(ValueError):
        client.embed_texts(
            [
                "texto válido",
                "   ",
            ]
        )
