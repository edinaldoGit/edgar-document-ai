import asyncio
from concurrent.futures import ThreadPoolExecutor

from ragas.embeddings.base import BaseRagasEmbeddings

from edgar.infrastructure.modal_text_embedder import ModalTextEmbedder


class RagasModalEmbeddings(BaseRagasEmbeddings):
    def __init__(
        self,
        *,
        embedder: ModalTextEmbedder,
    ):
        super().__init__()
        self._embedder = embedder

    def _embed_sync(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return self._embedder.embed(texts)

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self._embedder.embed,
                texts,
            )
            return future.result()

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        return self._embed_sync([text])[0]

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return self._embed_sync(texts)

    async def aembed_query(
        self,
        text: str,
    ) -> list[float]:
        embeddings = await self._embedder.aembed([text])
        return embeddings[0]

    async def aembed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return await self._embedder.aembed(texts)
