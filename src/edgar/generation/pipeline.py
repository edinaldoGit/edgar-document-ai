from uuid import UUID

from edgar.generation.contracts import AnswerGenerator
from edgar.generation.prompts import build_grounded_answer_prompt
from edgar.generation.results import AnswerResult
from edgar.retrieval.context import build_evidence_context
from edgar.retrieval.contracts import EvidenceRetriever

NO_EVIDENCE_ANSWER = "Não foram encontradas evidências suficientes para responder à pergunta."


class AnsweringPipeline:
    def __init__(
        self,
        *,
        retriever: EvidenceRetriever,
        generator: AnswerGenerator,
    ):
        self._retriever = retriever
        self._generator = generator

    def answer(
        self,
        question: str,
        *,
        limit: int = 5,
        doc_id: UUID | None = None,
    ) -> AnswerResult:
        question = question.strip()

        if not question:
            raise ValueError("Question must not be blank.")

        evidences = self._retriever.retrieve(
            question,
            limit=limit,
            doc_id=doc_id,
        )

        evidence_context = build_evidence_context(evidences)

        if evidence_context is None:
            return AnswerResult(
                question=question,
                answer=NO_EVIDENCE_ANSWER,
                evidences=(),
            )

        prompt = build_grounded_answer_prompt(
            question=question,
            evidence_context=evidence_context,
        )

        answer = self._generator.generate(
            prompt=prompt,
        ).strip()

        if not answer:
            raise RuntimeError("Answer generator returned a blank response.")

        return AnswerResult(
            question=question,
            answer=answer,
            evidences=tuple(evidences),
        )
