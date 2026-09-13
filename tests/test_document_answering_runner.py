from uuid import uuid4

from edgar.domain import Document
from edgar.generation.document_runner import (
    DocumentAnsweringRunner,
)
from edgar.generation.results import AnswerResult


class FakeIndexingRunner:
    def __init__(self):
        self.calls = []

    def run(self, document):
        self.calls.append(document)
        return []


class FakeAnsweringPipeline:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def answer(
        self,
        question,
        *,
        limit=5,
        doc_id=None,
    ):
        self.calls.append(
            (
                question,
                limit,
                doc_id,
            )
        )

        return self.result


def test_indexes_document_then_answers_question():
    document = Document(
        doc_id=uuid4(),
        filename="livro.pdf",
        source_ref="/tmp/livro.pdf",
        page_count=10,
    )

    expected = AnswerResult(
        question="Como o metro é definido?",
        answer=("O metro é definido pela distância percorrida pela luz [Evidence 1]."),
        evidences=(),
    )

    indexing_runner = FakeIndexingRunner()

    answering_pipeline = FakeAnsweringPipeline(expected)

    runner = DocumentAnsweringRunner(
        indexing_runner=indexing_runner,
        answering_pipeline=answering_pipeline,
    )

    result = runner.run(
        document,
        "Como o metro é definido?",
        limit=3,
    )

    assert result is expected

    assert indexing_runner.calls == [document]

    assert answering_pipeline.calls == [
        (
            "Como o metro é definido?",
            3,
            document.doc_id,
        )
    ]


def test_uses_default_retrieval_limit():
    document = Document(
        filename="livro.pdf",
        source_ref="/tmp/livro.pdf",
        page_count=1,
    )

    expected = AnswerResult(
        question="Pergunta",
        answer="Resposta",
        evidences=(),
    )

    answering_pipeline = FakeAnsweringPipeline(expected)

    runner = DocumentAnsweringRunner(
        indexing_runner=FakeIndexingRunner(),
        answering_pipeline=answering_pipeline,
    )

    runner.run(
        document,
        "Pergunta",
    )

    assert answering_pipeline.calls == [
        (
            "Pergunta",
            5,
            document.doc_id,
        )
    ]
