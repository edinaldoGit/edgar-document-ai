from edgar.infrastructure.modal_answer_generation_client import (
    ModalAnswerGenerationClient,
)


class ModalAnswerGenerator:
    def __init__(
        self,
        client: ModalAnswerGenerationClient,
        *,
        max_new_tokens: int = 256,
    ):
        if max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be positive.")

        self._client = client
        self._max_new_tokens = max_new_tokens

    def generate(
        self,
        *,
        prompt: str,
    ) -> str:
        result = self._client.generate(
            prompt,
            max_new_tokens=self._max_new_tokens,
        )

        answer = result.get("answer")

        if not isinstance(answer, str):
            raise RuntimeError("Answer generation service returned an invalid answer.")

        answer = answer.strip()

        if not answer:
            raise RuntimeError("Answer generation service returned a blank answer.")

        return answer
