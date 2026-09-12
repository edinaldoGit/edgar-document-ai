from edgar.infrastructure.modal_embedding_client import (
    ModalEmbeddingClient,
)


class ModalTextEmbedder:
    def __init__(
        self,
        *,
        client: ModalEmbeddingClient,
    ):
        self._client = client

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        response = self._client.embed_texts(
            texts,
        )

        embeddings = response.get("embeddings")

        if not isinstance(embeddings, list):
            raise RuntimeError("Modal embedding service returned invalid embeddings.")

        if len(embeddings) != len(texts):
            raise RuntimeError("Modal embedding service returned an unexpected embedding count.")

        result: list[list[float]] = []

        for embedding in embeddings:
            if not isinstance(embedding, list):
                raise RuntimeError("Modal embedding service returned an invalid embedding.")

            result.append([float(value) for value in embedding])

        return result
