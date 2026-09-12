import os
from io import BytesIO
from pathlib import Path
from time import perf_counter

import modal

APP_NAME = "edgar-visual-description-service"
MODEL_REPO = "Qwen/Qwen3-VL-4B-Instruct"
MODEL_CACHE_DIR = Path("/root/.cache/huggingface/models--Qwen--Qwen3-VL-4B-Instruct")
MAX_NEW_TOKENS = 384

app = modal.App(APP_NAME)

image = modal.Image.debian_slim(
    python_version="3.10",
).uv_pip_install(
    "torch==2.14.0",
    "torchvision==0.29.0",
    "transformers==5.17.0",
    "accelerate==1.15.0",
    "huggingface-hub==1.31.0",
    "pillow",
)

model_cache = modal.Volume.from_name(
    "edgar-model-cache",
)


@app.cls(
    image=image,
    gpu="T4",
    volumes={
        "/root/.cache/huggingface": model_cache,
    },
    max_containers=1,
    scaledown_window=30,
)
class VisualDescriptionService:
    @modal.enter()
    def load_model(self):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        from transformers import (
            AutoProcessor,
            Qwen3VLForConditionalGeneration,
        )

        revision = (MODEL_CACHE_DIR / "refs" / "main").read_text().strip()

        model_path = MODEL_CACHE_DIR / "snapshots" / revision

        if not model_path.is_dir():
            raise RuntimeError(f"Cached model snapshot not found: {model_path}")

        print(f"Loading cached model snapshot: {model_path}")

        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype="auto",
            device_map="auto",
            local_files_only=True,
        )

        self.processor = AutoProcessor.from_pretrained(
            model_path,
            local_files_only=True,
        )

    @modal.method()
    def describe(
        self,
        image_bytes: bytes,
        *,
        prompt: str,
        context: str | None = None,
    ):
        import torch
        from PIL import Image

        if not image_bytes:
            raise ValueError("Image bytes must not be empty.")

        if not prompt.strip():
            raise ValueError("Prompt must not be blank.")

        visual = Image.open(BytesIO(image_bytes)).convert("RGB")

        user_text = prompt.strip()

        if context is not None and context.strip():
            user_text = f"{user_text}\n\nContexto textual associado:\n{context.strip()}"

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": visual,
                    },
                    {
                        "type": "text",
                        "text": user_text,
                    },
                ],
            }
        ]

        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )

        inputs = inputs.to(self.model.device)

        start = perf_counter()

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
            )

        inference_seconds = perf_counter() - start

        trimmed_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(
                inputs.input_ids,
                generated_ids,
                strict=True,
            )
        ]

        description = self.processor.batch_decode(
            trimmed_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0].strip()

        return {
            "description": description or None,
            "inference_seconds": round(
                inference_seconds,
                4,
            ),
            "model": MODEL_REPO,
        }


@app.local_entrypoint()
def main(
    image_path: str,
    prompt: str,
    context: str = "",
):
    path = Path(image_path)

    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")

    service = VisualDescriptionService()

    result = service.describe.remote(
        path.read_bytes(),
        prompt=prompt,
        context=context or None,
    )

    print(result)
