import pytest

from edgar.generation.prompts import (
    build_grounded_answer_prompt,
)


def test_builds_grounded_answer_prompt():
    result = build_grounded_answer_prompt(
        question="Como o sistema trata PDFs sem texto nativo?",
        evidence_context=(
            "Evidence 1 | page=3 | type=plain_text | "
            "score=0.9123 | bbox=(10,20,300,120)\n"
            "O OCR é utilizado como fallback quando "
            "não existe camada textual nativa."
        ),
    )

    assert "Como o sistema trata PDFs sem texto nativo?" in result
    assert ("O OCR é utilizado como fallback quando não existe camada textual nativa.") in result
    assert "exclusivamente as evidências" in result
    assert "[Evidence N]" in result
    assert result.endswith("Resposta:")


def test_rejects_blank_question():
    with pytest.raises(ValueError):
        build_grounded_answer_prompt(
            question="   ",
            evidence_context="Evidence 1",
        )


def test_rejects_blank_evidence_context():
    with pytest.raises(ValueError):
        build_grounded_answer_prompt(
            question="Pergunta válida",
            evidence_context="   ",
        )
