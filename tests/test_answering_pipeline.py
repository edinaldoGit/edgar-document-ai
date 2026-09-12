from uuid import uuid4

import pytest

from edgar.domain import BoundingBox, ComponentType
from edgar.generation.pipeline import (
    NO_EVIDENCE_ANSWER,
    AnsweringPipeline,
)
from edgar.retrieval.results import RetrievedEvidence


class FakeRetriever:
    def __init__(self, evidences):
        self.evidences = evidences
        self.calls = []

    def retrieve(
        self,
        query,
        *,
        limit=5,
        doc_id=None,
    ):
        self.calls.append(
            (
                query,
                limit,
                doc_id,
            )
        )

        return self.evidences


class FakeGenerator:
    def __init__(self, answer):
        self.answer = answer
        self.prompts = []

    def generate(
        self,
        *,
        prompt,
    ):
        self.prompts.append(prompt)
        return self.answer


def make_evidence():
    return RetrievedEvidence(
        component_id=uuid4(),
        doc_id=uuid4(),
        page_index=2,
        component_type=ComponentType.PLAIN_TEXT,
        bbox=BoundingBox(
            x1=10,
            y1=20,
            x2=300,
            y2=120,
        ),
        text=("O OCR é utilizado como fallback quando não existe camada textual nativa."),
        score=0.91,
    )


def test_answers_using_retrieved_evidence():
    evidence = make_evidence()

    retriever = FakeRetriever([evidence])

    generator = FakeGenerator("O sistema utiliza OCR como fallback [Evidence 1].")

    pipeline = AnsweringPipeline(
        retriever=retriever,
        generator=generator,
    )

    doc_id = uuid4()

    result = pipeline.answer(
        "  Como o sistema trata PDFs sem texto nativo?  ",
        limit=3,
        doc_id=doc_id,
    )

    assert result.question == ("Como o sistema trata PDFs sem texto nativo?")

    assert result.answer == ("O sistema utiliza OCR como fallback [Evidence 1].")

    assert result.evidences == (evidence,)

    assert retriever.calls == [
        (
            "Como o sistema trata PDFs sem texto nativo?",
            3,
            doc_id,
        )
    ]

    assert len(generator.prompts) == 1
    assert "Evidence 1" in generator.prompts[0]
    assert evidence.text in generator.prompts[0]


def test_does_not_call_generator_without_evidence():
    retriever = FakeRetriever([])
    generator = FakeGenerator("não deve ser usado")

    pipeline = AnsweringPipeline(
        retriever=retriever,
        generator=generator,
    )

    result = pipeline.answer(
        "Pergunta sem evidência",
    )

    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.evidences == ()
    assert generator.prompts == []


def test_rejects_blank_question():
    pipeline = AnsweringPipeline(
        retriever=FakeRetriever([]),
        generator=FakeGenerator("resposta"),
    )

    with pytest.raises(ValueError):
        pipeline.answer("   ")


def test_rejects_blank_generated_answer():
    pipeline = AnsweringPipeline(
        retriever=FakeRetriever([make_evidence()]),
        generator=FakeGenerator("   "),
    )

    with pytest.raises(RuntimeError):
        pipeline.answer("Pergunta válida")
