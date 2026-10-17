import asyncio

from langchain_core.outputs import Generation, LLMResult
from langchain_core.prompt_values import PromptValue
from ragas.llms.base import BaseRagasLLM

from edgar.infrastructure.modal_answer_generator import ModalAnswerGenerator


class RagasModalLLM(BaseRagasLLM):
    def __init__(
        self,
        *,
        generator: ModalAnswerGenerator,
    ):
        super().__init__(
            multiple_completion_supported=False,
        )
        self._generator = generator

    def generate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float = 0.01,
        stop: list[str] | None = None,
        callbacks=None,
    ) -> LLMResult:
        if n != 1:
            raise ValueError("RagasModalLLM supports only one completion per request.")

        answer = self._generator.generate(
            prompt=prompt.to_string(),
        )

        return LLMResult(
            generations=[
                [
                    Generation(
                        text=answer,
                    )
                ]
            ]
        )

    async def agenerate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float | None = 0.01,
        stop: list[str] | None = None,
        callbacks=None,
    ) -> LLMResult:
        return await asyncio.to_thread(
            self.generate_text,
            prompt,
            n,
            0.01 if temperature is None else temperature,
            stop,
            callbacks,
        )

    def is_finished(
        self,
        response: LLMResult,
    ) -> bool:
        if not response.generations:
            return False

        first_group = response.generations[0]

        if not first_group:
            return False

        return bool(first_group[0].text.strip())
