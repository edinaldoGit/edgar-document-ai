import pytest

from edgar.infrastructure.modal_answer_generator import (
    ModalAnswerGenerator,
)


class FakeClient:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate(
        self,
        prompt,
        *,
        max_new_tokens=256,
    ):
        self.calls.append(
            (
                prompt,
                max_new_tokens,
            )
        )

        return self.result


def test_generates_answer_using_modal_client():
    client = FakeClient({"answer": ("O sistema utiliza OCR como fallback [Evidence 1].")})

    generator = ModalAnswerGenerator(
        client,
        max_new_tokens=128,
    )

    result = generator.generate(
        prompt="Prompt fundamentado",
    )

    assert result == ("O sistema utiliza OCR como fallback [Evidence 1].")

    assert client.calls == [
        (
            "Prompt fundamentado",
            128,
        )
    ]


def test_strips_generated_answer():
    generator = ModalAnswerGenerator(
        FakeClient(
            {
                "answer": "  resposta  ",
            }
        )
    )

    assert (
        generator.generate(
            prompt="Prompt",
        )
        == "resposta"
    )


def test_rejects_invalid_token_limit():
    with pytest.raises(ValueError):
        ModalAnswerGenerator(
            FakeClient({}),
            max_new_tokens=0,
        )


def test_rejects_missing_answer():
    generator = ModalAnswerGenerator(FakeClient({}))

    with pytest.raises(RuntimeError):
        generator.generate(
            prompt="Prompt",
        )


def test_rejects_blank_answer():
    generator = ModalAnswerGenerator(
        FakeClient(
            {
                "answer": "   ",
            }
        )
    )

    with pytest.raises(RuntimeError):
        generator.generate(
            prompt="Prompt",
        )
