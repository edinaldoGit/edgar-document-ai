from typing import Protocol


class TextEmbedder(Protocol):
    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]: ...
