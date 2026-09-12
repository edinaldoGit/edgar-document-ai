import pytest

from edgar.infrastructure.modal_text_embedder import (
    ModalTextEmbedder,
)


class FakeEmbeddingClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def embed_texts(self, texts):
        self.calls.append(texts)
        return self.response


def test_converts_modal_response_to_embeddings():
    client = FakeEmbeddingClient(
        {
            "embeddings": [
                [0.1, 0.2],
                [0.3, 0.4],
            ],
            "dimension": 2,
            "count": 2,
        }
    )

    embedder = ModalTextEmbedder(
        client=client,
    )

    result = embedder.embed(
        [
            "texto um",
            "texto dois",
        ]
    )

    assert result == [
        [0.1, 0.2],
        [0.3, 0.4],
    ]


def test_rejects_wrong_embedding_count():
    client = FakeEmbeddingClient(
        {
            "embeddings": [
                [0.1, 0.2],
            ],
        }
    )

    embedder = ModalTextEmbedder(
        client=client,
    )

    with pytest.raises(RuntimeError):
        embedder.embed(
            [
                "texto um",
                "texto dois",
            ]
        )
