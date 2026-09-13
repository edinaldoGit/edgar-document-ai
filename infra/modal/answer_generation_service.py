import os
import time
from pathlib import Path

import modal

APP_NAME = "edgar-answer-generation-service"
MODEL_REPO = "Qwen/Qwen2.5-7B-Instruct"
MODEL_CACHE_DIR = Path("/root/.cache/huggingface/models--Qwen--Qwen2.5-7B-Instruct")

app = modal.App(APP_NAME)

model_cache = modal.Volume.from_name("edgar-model-cache")

image = modal.Image.debian_slim(
    python_version="3.10",
).uv_pip_install(
    "torch==2.14.0",
    "transformers==5.17.0",
    "accelerate==1.15.0",
    "bitsandbytes",
    "huggingface-hub==1.31.0",
)


@app.cls(
    image=image,
    gpu="T4",
    volumes={
        "/root/.cache/huggingface": model_cache,
    },
    timeout=900,
    scaledown_window=30,
    max_containers=1,
)
class AnswerGenerationService:
    @modal.enter()
    def load(self):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
        )

        revision = (MODEL_CACHE_DIR / "refs" / "main").read_text().strip()

        model_path = MODEL_CACHE_DIR / "snapshots" / revision

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

        started = time.perf_counter()

        self.tokenizer = AutoTokenizer.from_pretrained(
            str(model_path),
            local_files_only=True,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            local_files_only=True,
            quantization_config=quantization_config,
            device_map="auto",
            low_cpu_mem_usage=True,
        )

        self.load_seconds = time.perf_counter() - started

    @modal.method()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 256,
    ) -> dict:
        import torch

        prompt = prompt.strip()

        if not prompt:
            raise ValueError("Prompt must not be blank.")

        if max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be positive.")

        messages = [
            {
                "role": "system",
                "content": (
                    "Você é o módulo de geração "
                    "fundamentada do sistema EDGAR. "
                    "Use somente informações explicitamente "
                    "presentes nas evidências fornecidas. "
                    "Não acrescente conhecimento externo, "
                    "definições ou expansões de siglas."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        chat_prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            chat_prompt,
            return_tensors="pt",
        ).to(self.model.device)

        started = time.perf_counter()

        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
            )

        generation_seconds = time.perf_counter() - started

        generated = output[
            0,
            inputs["input_ids"].shape[1] :,
        ]

        answer = self.tokenizer.decode(
            generated,
            skip_special_tokens=True,
        ).strip()

        return {
            "answer": answer,
            "model": MODEL_REPO,
            "generation_seconds": (generation_seconds),
            "load_seconds": self.load_seconds,
        }


@app.local_entrypoint()
def main():
    service = AnswerGenerationService()

    result = service.generate.remote(
        (
            "Responda exclusivamente com base "
            "na evidência fornecida.\n\n"
            "Pergunta:\n"
            "Como o sistema trata PDFs sem texto "
            "nativo?\n\n"
            "Evidências:\n"
            "Evidence 1 | page=3 | "
            "type=plain_text | score=0.9123 | "
            "bbox=(10,20,300,120)\n"
            "O OCR é utilizado como fallback quando "
            "não existe camada textual nativa.\n\n"
            "Ao sustentar a resposta, cite "
            "[Evidence 1]."
        ),
        max_new_tokens=80,
    )

    print("Resposta:")
    print(result["answer"])
    print()
    print(
        "Generation seconds:",
        round(
            result["generation_seconds"],
            2,
        ),
    )
    print(
        "Load seconds:",
        round(
            result["load_seconds"],
            2,
        ),
    )
