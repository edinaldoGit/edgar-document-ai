import os
from pathlib import Path
from time import perf_counter

import modal

APP_NAME = "edgar-embedding-service"
MODEL_REPO = "BAAI/bge-m3"
MODEL_CACHE_DIR = Path("/root/.cache/huggingface/models--BAAI--bge-m3")

app = modal.App(APP_NAME)

image = modal.Image.debian_slim(
    python_version="3.10",
).uv_pip_install(
    "sentence-transformers==6.0.1",
    "huggingface-hub==1.31.0",
)

model_cache = modal.Volume.from_name(
    "edgar-model-cache",
)


@app.cls(
    image=image,
    volumes={
        "/root/.cache/huggingface": model_cache,
    },
    max_containers=1,
    scaledown_window=30,
)
class EmbeddingService:
    @modal.enter()
    def load_model(self):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        from sentence_transformers import SentenceTransformer

        revision = (MODEL_CACHE_DIR / "refs" / "main").read_text().strip()

        model_path = MODEL_CACHE_DIR / "snapshots" / revision

        if not model_path.is_dir():
            raise RuntimeError(f"Cached model snapshot not found: {model_path}")

        print(f"Loading cached embedding model: {model_path}")

        self.model = SentenceTransformer(
            str(model_path),
            local_files_only=True,
        )

    @modal.method()
    def embed(
        self,
        texts: list[str],
    ):
        if not texts:
            raise ValueError("Texts must not be empty.")

        if any(not text.strip() for text in texts):
            raise ValueError("Texts must not contain blank values.")

        start = perf_counter()

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )

        elapsed = perf_counter() - start

        return {
            "embeddings": embeddings.tolist(),
            "dimension": int(embeddings.shape[1]),
            "count": int(embeddings.shape[0]),
            "embed_seconds": round(
                elapsed,
                4,
            ),
            "model": MODEL_REPO,
        }


@app.local_entrypoint()
def main():
    service = EmbeddingService()

    result = service.embed.remote(
        [
            "Arquiteturas RAG recuperam evidências.",
            "EDGAR trabalha com componentes documentais.",
        ]
    )

    print(
        {
            "dimension": result["dimension"],
            "count": result["count"],
            "embed_seconds": result["embed_seconds"],
            "model": result["model"],
        }
    )
